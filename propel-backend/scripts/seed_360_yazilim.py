"""
360° Feedback Seed — Yazılım Geliştirme + Satış Departmanı (4 hafta × tüm çalışanlar)

Oluşturur:
  - FeedbackQuestion  → 4 hafta × 3 yön × 2 departman
  - FeedbackResponse  → her çalışan 3-4 geri bildirim alır (Mayıs + Haziran 2026)
  - FeedbackNLPAnalysis → her response için analiz
  - EmployeeNLPProfile  → her çalışan × her period için özet
"""

import sys, os, random
from datetime import date

sys.path.insert(0, "/app")

from app.db.session import SessionLocal
from app.db.models.feedback import (
    FeedbackQuestion, FeedbackResponse, FeedbackDirection,
)
from app.db.models.nlp import (
    FeedbackNLPAnalysis, EmployeeNLPProfile,
    NLPSourceType, NLPPeriodType, RiskLevel, SentimentLabel,
)
from app.db.models.employee import Employee

db = SessionLocal()

RESET = "--reset" in sys.argv

# ── Sabitler ─────────────────────────────────────────────────────────────────
YAZILIM_DEPT_ID = 21
SATIS_DEPT_ID   = 22

WEEKLY_THEMES = {
    1: "Süreçler & Blokajlar",
    2: "Motivasyon & Psikolojik Durum",
    3: "İş Birliği & Şeffaflık",
    4: "Gelişim & Vizyon",
}

# Tohumlanacak dönemler: (year, month, week)
PERIODS = [
    (2026, 4, 1), (2026, 4, 2), (2026, 4, 3), (2026, 4, 4),
    (2026, 5, 1), (2026, 5, 2), (2026, 5, 3), (2026, 5, 4),
    (2026, 6, 1),
]
CURRENT_PERIOD = (2026, 6, 1)

# ── Soru metinleri ─────────────────────────────────────────────────────────
YAZILIM_QUESTIONS = [
    # (week, direction, category, text)
    (1, FeedbackDirection.peer_to_peer,
     "Süreçler & Blokajlar",
     "Bu hafta iş arkadaşının sprint sürecinde karşılaştığı bir blokajı nasıl ele aldığını gözlemledin? "
     "Pull request kalitesi ve bug çözme hızı açısından somut bir örnek ver; bu durumun ekip velocity'sine etkisi ne oldu?"),

    (2, FeedbackDirection.peer_to_peer,
     "Motivasyon & Psikolojik Durum",
     "Bu hafta iş arkadaşının motivasyon ve enerji seviyesini nasıl gözlemledin? "
     "Ekip hedeflerine olan bağlılığı ve aidiyet hissi açısından somut bir örnekle anlat; "
     "psikolojik güven konusunda destek ihtiyacı var mı?"),

    (3, FeedbackDirection.peer_to_peer,
     "İş Birliği & Şeffaflık",
     "Bu hafta iş arkadaşının code review katkıları ve ekip içi iletişim kalitesi nasıldı? "
     "Kriz veya zorluk anında nasıl davrandığını somut bir örnekle anlat."),

    (4, FeedbackDirection.peer_to_peer,
     "Gelişim & Vizyon",
     "Bu hafta iş arkadaşının dokümantasyon disiplini ve yeni kütüphanelere adaptasyon konusunda "
     "gözlemlediğin somut bir gelişim ya da durgunluk örneği nedir? Kariyer hedefleri hakkında ipuçları aldın mı?"),

    (3, FeedbackDirection.manager_to_employee,
     "İş Birliği & Şeffaflık",
     "Bu hafta ekip üyesinin teknik borç yönetimi, kod kalitesi standartlarına uyumu ve ekip içi "
     "şeffaflık davranışları nasıldı? Mentorluk açısından destek ihtiyacı gözlemledin mi?"),

    (4, FeedbackDirection.employee_to_manager,
     "Gelişim & Vizyon",
     "Bu hafta yöneticinizin ekipteki blokajları kaldırma hızı ve mentorluk kalitesi nasıldı? "
     "Sprint planlama ve ekip velocity'sine katkısı ile gelişim desteği açısından somut bir örnek verir misiniz?"),
]

SATIS_QUESTIONS = [
    (1, FeedbackDirection.peer_to_peer,
     "Süreçler & Blokajlar",
     "Bu hafta iş arkadaşının pipeline yönetimi ve takip disiplini konusunda karşılaştığı blokajları "
     "nasıl ele aldığını gözlemledin? CRM hijyeni ve hedef kapama disiplini açısından somut bir örnek ver."),

    (2, FeedbackDirection.peer_to_peer,
     "Motivasyon & Psikolojik Durum",
     "Bu hafta iş arkadaşının motivasyon ve satış enerjisini nasıl gözlemledin? "
     "Müşteri görüşmelerindeki tutumu ve ekip hedeflerine bağlılığı açısından bir örnek ver; "
     "psikolojik güven konusunda destek ihtiyacı var mı?"),

    (3, FeedbackDirection.peer_to_peer,
     "İş Birliği & Şeffaflık",
     "Bu hafta iş arkadaşının ekip içi iletişim ve bilgi paylaşımı kalitesi nasıldı? "
     "Müşteri itirazlarını nasıl yönettiğini ve ekibe destek davranışını somut örnekle anlat."),

    (4, FeedbackDirection.peer_to_peer,
     "Gelişim & Vizyon",
     "Bu hafta iş arkadaşının lead dönüşüm kalitesi ve kapatma becerisi konusunda gözlemlediğin "
     "gelişim ya da durgunluk örneği nedir? Satış hedeflerine yönelik uzun vadeli düşünce sergiliyor mu?"),

    (3, FeedbackDirection.manager_to_employee,
     "İş Birliği & Şeffaflık",
     "Bu hafta ekip üyesinin müşteri güveni oluşturma, itiraz yönetimi ve CRM kayıt disiplini "
     "nasıldı? Ekip kochluğu açısından hangi desteği verdin?"),

    (4, FeedbackDirection.employee_to_manager,
     "Gelişim & Vizyon",
     "Bu hafta yöneticinizin tahmin doğruluğu, ekip koçluğu ve pipeline yönetimine katkısı nasıldı? "
     "Hedef kapama disiplini ve ekibin önündeki engelleri kaldırma becerisi açısından somut bir örnek verir misiniz?"),
]

# ── Çalışan profilleri ───────────────────────────────────────────────────────
# Profil: (sentiment, burnout, flight, psych_safety, collab, growth, leadership)
PROFILES = {
    "high": {
        "sentiment": (SentimentLabel.positive, 0.82, 0.88),
        "burnout": RiskLevel.low, "flight": RiskLevel.low,
        "psych": (0.8, 0.95), "collab": (0.78, 0.92),
        "growth": (0.75, 0.90), "leadership": (0.7, 0.88),
        "scores": (4, 5),
    },
    "medium": {
        "sentiment": (SentimentLabel.neutral, 0.45, 0.65),
        "burnout": RiskLevel.medium, "flight": RiskLevel.low,
        "psych": (0.5, 0.72), "collab": (0.55, 0.72),
        "growth": (0.48, 0.68), "leadership": (0.45, 0.65),
        "scores": (3, 4),
    },
    "atrisk": {
        "sentiment": (SentimentLabel.negative, 0.15, 0.38),
        "burnout": RiskLevel.high, "flight": RiskLevel.high,
        "psych": (0.15, 0.38), "collab": (0.2, 0.42),
        "growth": (0.18, 0.40), "leadership": (0.15, 0.38),
        "scores": (1, 3),
    },
    "medium_risk": {
        "sentiment": (SentimentLabel.neutral, 0.38, 0.55),
        "burnout": RiskLevel.medium, "flight": RiskLevel.medium,
        "psych": (0.32, 0.52), "collab": (0.35, 0.55),
        "growth": (0.30, 0.50), "leadership": (0.28, 0.48),
        "scores": (2, 3),
    },
}

# Yazılım çalışan → profil ataması (emp_id: profile_key)
YAZILIM_PROFILES = {
    194: "high",        # MGR-SW — yönetici
    197: "high",        # SE-001
    198: "medium",      # SE-004
    199: "medium",      # SE-005
    200: "medium",      # SE-006
    201: "high",        # SE-007
    202: "high",        # SE-009
    203: "atrisk",      # SE-010
    204: "medium_risk", # SE-013
    205: "high",        # SE-014
    206: "medium",      # SE-016
    207: "high",        # SE-017
    208: "medium",      # SE-018
    209: "atrisk",      # SE-020
    210: "high",        # SE-025
    211: "medium",      # SE-026
    212: "atrisk",      # SE-027
    213: "medium_risk", # SE-028
    214: "medium",      # SE-031
    215: "atrisk",      # SE-032
    216: "medium",      # SE-033
    217: "atrisk",      # SE-034
    218: "medium_risk", # SE-035
    219: "atrisk",      # SE-038
    220: "medium_risk", # SE-040
    221: "high",        # SE-042
    222: "medium",      # SE-045
    223: "high",        # SE-046
    224: "medium_risk", # SE-047
    225: "medium",      # SE-048
    226: "high",        # SE-049
}

# ── Yanıt metinleri ──────────────────────────────────────────────────────────
# (profile, week, dept) → list of response templates
SW_TEXTS = {
    # HIGH — Yazılım
    ("high", 1, "sw"): [
        "Bu hafta sprint sürecinde çok kritik bir blokajla karşılaşıldığında harika bir problem çözme becerisi sergiledi. "
        "Özellikle authentication servisindeki bug'ı hızla tespit etti ve pull request kalitesi çok yüksekti; "
        "tüm edge case'leri düşünmüştü. Test disiplinini asla ihmal etmiyor, ekip velocity'sine somut katkısı çok belirgin. "
        "Hiç geri çekilmeden diğer ekip üyelerine de destek oldu.",

        "Hafta boyunca code review süreçlerini sahiplendi; her PR'ı ayrıntılı inceleyerek yapıcı geri bildirim verdi. "
        "CI/CD pipeline'da oluşan bir blokajı kendi inisiyatifiyle çözdü. "
        "Teknik borç riski taşıyan bir modülü önceden fark edip liderliğe bildirdi. "
        "Ekip velocity üzerindeki etkisi kesinlikle pozitif; güven veren ve hevesli biri.",

        "Sprint planlama toplantısında blokajları ilk fark eden o oldu. Bug çözme hızı etkileyiciydi, "
        "kritik bir production hatasını 2 saat içinde düzeltti. "
        "Pull request'lerindeki test coverage eksiksizdi. Kopma ya da tükenmişlik sinyali hiç gözlemlemedim.",
    ],
    ("high", 2, "sw"): [
        "Bu hafta motivasyonu ve enerjisi çok yüksekti. Ekip hedeflerine olan bağlılığı herkese ilham veriyor. "
        "Özellikle zor bir sprint döneminde bile istekli ve sahiplenme duygusuyla çalıştı. "
        "Aidiyet hissi çok güçlü, psikolojik güven açısından ekibe olumlu enerji katıyor. "
        "Tükenmişlik ya da kopma sinyali kesinlikle yok.",

        "Motivasyon trendi bu hafta da yüksek seyretti. Fazla mesai gerektiren bir görevde gönüllü oldu, "
        "şikayet etmedi. Ekip atmosferini olumlu etkiliyor. Psikolojik güven açısından mükemmel duruyor; "
        "herkes fikirlerini özgürce paylaşabiliyor yanında. Destek ihtiyacı görmüyorum, tam tersine desteği o sağlıyor.",

        "Yoğun bir haftada bile enerji seviyesi hiç düşmedi. Ekip üyelerine motivasyon aşılayan tutumu gözlemledim. "
        "Hedeflere olan inancı sağlam, aidiyet hissi çok belirgin. "
        "Psikolojik güvenlik ortamına çok katkı sağlıyor.",
    ],
    ("high", 3, "sw"): [
        "Code review katkıları bu hafta da mükemmeldi. Kriz anında sakin kaldı, çözüm odaklı yaklaştı. "
        "Bir deployment sorunu yaşandığında paniklemek yerine sistematik bir yaklaşım benimsedi. "
        "Ekip içi iletişim kalitesi çok yüksek; bilgiyi saklamaması ve şeffaf davranması ekibe büyük artı sağlıyor.",

        "Teknik bir anlaşmazlıkta arabuluculuk yaptı, iki tarafın da bakış açısını dinleyerek uzlaşı sağladı. "
        "İletişim kalitesi son derece yüksek, bilgiyi ekiple aktif paylaşıyor. "
        "Code review'larda yapıcı ve öğretici geri bildirimler veriyor. Ekip enerjisine olumlu etkisi çok belirgin.",

        "Zorlu bir sprint review'da geri bildirim almaktan çekinmedi ve aynı hatayı tekrar etmedi. "
        "Şeffaf iletişimi ekip güvenini güçlendiriyor. "
        "Kriz anında yardım isteme cesareti var, bu psikolojik güvenliği besliyor.",
    ],
    ("high", 4, "sw"): [
        "Bu hafta yeni bir framework'e adaptasyonu etkileyiciydi. Dökümantasyon disiplini çok yüksek; "
        "yazdığı teknik belgeler net ve kapsamlı. Kariyer hedefleri konusunda konuştuğumuzda "
        "şirkette uzun vadeli büyüme planladığını hissettirdi. Öğrenme isteği açıkça görülüyor.",

        "Gelişim açısından bu hafta somut bir adım attı: yeni bir test kütüphanesi öğrendi ve ekiple paylaştı. "
        "Dökümantasyonu güncel tutuyor, teknik yazısı açık ve okunabilir. "
        "Kariyer vizyonu net; yaptığı işte anlam ve gelişim buluyor.",

        "Yeni kütüphane adaptasyonunda öncü rol üstlendi ve bunu ekiple paylaşmaktan keyif aldı. "
        "Öğrenme disiplini çok güçlü, gelişim sahiplenme sinyali yüksek. "
        "Durgunluk ya da kariyer belirsizliği sinyali gözlemlemedim.",
    ],

    # MEDIUM — Yazılım
    ("medium", 1, "sw"): [
        "Sprint sürecinde blokajlarını gecikmeli bildirdi; bu durum ekip velocity'sini biraz yavaşlattı. "
        "Pull request kalitesi genellikle yeterli ama bazen test coverage eksik kalabiliyor. "
        "Bug çözme hızı orta düzeyde; acil sorunlarda daha hızlı davranması gerekiyor. "
        "Genel olarak stabil, ciddi bir risk sinyali görmüyorum.",

        "Bu hafta bir blokajla karşılaştı ama çözümde destek istedi; bağımsız inisiyatif alması biraz zayıf. "
        "PR'larında testler mevcut ama coverage %70'in altında kaldı. "
        "Ekip velocity'sine net etkisi nötr. Daha proaktif olmasını bekliyorum.",

        "Süreç disiplini makul ama tutarsız. Blokajı erkenden fark etti fakat bildirmekte tereddüt etti. "
        "Pull request geri bildirimlerine açık, düzeltmeleri hızla yapıyor. "
        "Genel gidişat iyi, motivasyon düşüşü ya da kopma sinyali gözlemlemedim.",
    ],
    ("medium", 2, "sw"): [
        "Bu hafta motivasyonu dengeli görünüyordu. Özellikle sprintin ortasında biraz enerji kaybı yaşadı "
        "ama hafta sonuna doğru toparladı. Ekip hedeflerine genel olarak bağlı; "
        "psikolojik güven açısından stabil. Net bir tükenmişlik sinyali yok.",

        "Motivasyon seviyesi sabit ama yüksek enerjili değil. Rutin görevlerde iyi iş çıkarıyor, "
        "zorlu problemlerde biraz çekingen kalabiliyor. "
        "Aidiyet hissi makul; büyük risk sinyali görmüyorum ama destek görmesi işe yarar.",

        "Bu hafta enerji seviyesi orta düzeydeydi. Sprint hedeflerine ulaştı ama çok hevesli değildi. "
        "Psikolojik güven ortamında rahat görünüyor, ekip atmosferini olumlu etkiliyor. "
        "Motivasyon düşüşü başlamadan önce gelişim fırsatı sunmak iyi olur.",
    ],
    ("medium", 3, "sw"): [
        "Code review katkıları yeterli düzeyde, ancak her zaman ayrıntılı geri bildirim vermiyor. "
        "Bir zorluk anında sessiz kaldı ve yardım istemekte gecikti. "
        "İletişim kalitesi makul; bilgiyi aktif olarak paylaşmıyor ama sorulduğunda yardımcı oluyor.",

        "Ekip içi iletişimde bazen geri planda kalıyor. Code review süreçlerine katılıyor ama "
        "derin yorumlar yapmaktan kaçınıyor. Kriz anında paniklemeden durumu yönetti, "
        "iyi bir soğukkanlılık sergiledi.",

        "Bu hafta iletişim kalitesi orta düzeydeydi. Teknik bilgisini paylaşmakta biraz çekingen. "
        "Code review'larda genellikle yüzeysel yorum yapıyor, derinlemesine analiz eksik. "
        "Ekip güvenine katkısı var ama daha aktif bir rol üstlenebilir.",
    ],
    ("medium", 4, "sw"): [
        "Gelişim konusunda fırsatları değerlendiriyor ama hız makul düzeyde. "
        "Dökümantasyon bazen eksik kalıyor, özellikle karmaşık modüllerde. "
        "Yeni kütüphane konusunda öğrenme isteği var ama adaptasyon süresi biraz uzuyor. "
        "Kariyer planı belirsiz ama şirketten ayrılma sinyali yok.",

        "Bu hafta yeni bir framework bileşenini öğrendi; öğrenme süreci biraz yavaş ama kararlı. "
        "Dökümantasyon disiplini geliştirilmeli; teknik belgeler zaman zaman eksik veya eski kalıyor. "
        "Kariyer hedefleri hakkında konuşmak isteyebilir, mentorluk desteği faydalı olur.",

        "Gelişim isteği var ancak uygulama disiplininde tutarsızlık görülüyor. "
        "Yeni yaklaşımları denemekten çekinmiyor; bu olumlu bir sinyal. "
        "Kariyer vizyonu biraz bulanık, yönlendirmeye ihtiyaç duyabilir.",
    ],

    # ATRISK — Yazılım
    ("atrisk", 1, "sw"): [
        "Bu hafta ciddi blokajlar yaşadı ve bunları zamanında bildirmedi; bu ekip velocity'sini olumsuz etkiledi. "
        "Pull request'lerinde önemli test eksiklikleri vardı. "
        "Teknik borç biriktiğini hissediyorum, blokajları çözülmeden birikiyor. "
        "Motivasyon kaybi fark ettim; toplantılarda çok geri çekiliyor, aidiyet hissi zayıflamış gibi.",

        "Sprint sürecinde blokajları saklamaya çalıştı, bu ciddi bir sorun. "
        "PR kalitesi düşüktü, code review sürecinde dikkat dağınıklığı belliydi. "
        "Kendisiyle konuştuğumda yorgunluk ve tükenme belirtileri gözlemledim. "
        "Ayrılmayı düşündüğünü ima etti, bu konuyu yöneticinin bilmesi gerekiyor.",

        "Bu hafta performansı belirgin biçimde düştü. Blokajları çözmeye çalışmak yerine görmezden geldi. "
        "Test disiplini neredeyse yok. Ekip velocity'sine etkisi olumsuz. "
        "Tükenmişlik sinyalleri açık: molalarını atlıyor, fazla mesaiyi reddediyor, "
        "sorulara kısa ve kaçamak cevaplar veriyor.",
    ],
    ("atrisk", 2, "sw"): [
        "Bu hafta motivasyon düşüşü çok belirgin. Ekip hedeflerine olan inancını yitirmiş gibi görünüyor. "
        "Toplantılarda ilgisiz kalıyor, aidiyet hissi ciddi ölçüde azalmış. "
        "Tükenmişlik sinyalleri endişe verici; konuştuğumuzda 'bunu ne kadar daha yapabilirim' dedi. "
        "Psikolojik güven açısından kendini güvende hissetmiyor, destek ihtiyacı acil.",

        "Enerji seviyesi son derece düşük. Ekip aktivitelerinden uzaklaşıyor, kopma sinyali net. "
        "Motivasyon kaybı sadece bu haftaya özgü değil; son birkaç haftadan beri devam ediyor. "
        "İşten ayrılmayı değerlendirdiğini çevresine ima ettiğini duydum. Acil müdahale gerekiyor.",

        "Bu hafta aidiyet hissi ve ekibe bağlılık ciddi ölçüde zayıflamış durumda. "
        "Hedeflere olan inancını yitirmiş, işin anlamını sorguluyor gibi. "
        "Psikolojik güven ortamında rahat değil; fikirlerini paylaşmaktan kaçınıyor. "
        "Tükenmişlik riski yüksek, yöneticinin acil görüşme planlamasını öneririm.",
    ],
    ("atrisk", 3, "sw"): [
        "Code review süreçlerine katılımı bu hafta neredeyse sıfıra indi. "
        "Ekip içi iletişimde giderek daha kapalı bir tutum sergiliyor; bilgi paylaşımından kaçınıyor. "
        "Zorlu bir anda ekibi yalnız bıraktı, destek vermek yerine geri çekildi. "
        "İş birliği sinyali çok zayıf; şeffaflık tamamen kaybolmuş.",

        "Bu hafta ekip içi iletişim kalitesi çok düştü. Toplantılarda söz almıyor, "
        "sorularını iletiyor ama cevapları beklemiyor gibi davranıyor. "
        "Code review yorumları yok veya anlamsız derecede kısa. "
        "Kopma ve ayrışma sinyali bu alanda da kendini gösteriyor.",

        "İletişim kalitesi ciddi şekilde bozulmuş. Ekip içinde güven kurmaya çalışmıyor; "
        "aksine mesafe koyuyor. Kriz anında destek vermek yerine çekildi. "
        "Bu durum ekip enerjisini olumsuz etkiliyor.",
    ],
    ("atrisk", 4, "sw"): [
        "Gelişim açısından durgunluk var; yeni şeyler öğrenmeye karşı dirençli bir tutum sergiliyor. "
        "Dökümantasyon görevlerini sürekli erteliyor, uyarılara rağmen düzeltmiyor. "
        "Kariyer konusunda konuştuğumuzda 'zaten fark etmez' dedi; bu çok endişe verici. "
        "Sahiplenme ve büyüme sinyali tamamen yok.",

        "Bu hafta hiçbir gelişim inisiyatifi almadı. Yeni kütüphaneleri öğrenmekten kaçınıyor, "
        "rutin işleri bitirip kaçmak istiyor gibi. Dökümantasyon çok eksik. "
        "Kariyer belirsizliği değil, kariyer ilgisizliği var; bu ayrılma sinyaliyle örtüşüyor.",

        "Gelişim ve öğrenme tamamen durdu. Dökümantasyon disiplini yok. "
        "Kariyer hedefleri hakkında konuşmak istemedi. Durgunluk sinyali çok belirgin, "
        "sahiplenme duygusu kalmamış gibi.",
    ],

    # MEDIUM_RISK — Yazılım
    ("medium_risk", 1, "sw"): [
        "Bu hafta blokajlarını geç bildirdi; ekip velocity'sini olumsuz etkiledi. "
        "Pull request kalitesi düşük; test coverage yetersiz ve bazı kritik durumlar atlandı. "
        "Motivasyon dalgalanıyor, zaman zaman ilgisizlik gözlemliyorum. "
        "Küçük bir risk sinyali var, yakından takip edilmeli.",

        "Sprint sürecinde blokajlara karşı tutumu pasif kaldı. PR'larda tekrar eden hatalar var. "
        "Stres altında performansı biraz düşüyor. "
        "Ayrılma niyeti net değil ama bazı yorumları endişe uyandırıyor. Destek faydalı olur.",

        "Süreç akışında tutarsızlıklar var. Blokajları tek başına çözmeye çalışıyor ama yardım istemekte direnç var. "
        "Ekip üzerine olumsuz yük bindiriyor farkında olmadan. "
        "Motivasyon kaybi başlangıç aşamasında, henüz geri dönülebilir.",
    ],
    ("medium_risk", 2, "sw"): [
        "Motivasyon seviyesi bu hafta dalgalıydı; başlangıçta iyi sonra düşüş yaşadı. "
        "Ekip hedeflerine olan bağlılığında soru işaretleri var. "
        "Aidiyet hissi zayıflıyor, psikolojik güvende belirsizlik var. "
        "Burnout başlangıcı olabilir; yakından izlenmeli.",

        "Bu hafta stres altındaydı ve bunu ekiple paylaşmakta zorlandı. "
        "Enerji seviyesi düşüktü, performansı etkilendi. "
        "İşten ayrılma sinyali net değil ama 'yoruldum' ifadesini birkaç kez kullandı. "
        "Destek ihtiyacı orta düzeyde.",

        "Motivasyon düşüşü fark edilir boyuta geldi. Toplantılarda aktif katılımı azaldı. "
        "Ekip hedeflerine bağlılık sallantılı. Psikolojik güven açısından bazı sinyaller endişe verici. "
        "Erken müdahale faydalı olur.",
    ],
    ("medium_risk", 3, "sw"): [
        "Code review'lara katılıyor ama yorumları yüzeysel. "
        "İletişimde bazen gergin anlar yaşandı; kriz anında sakinliğini koruyamadı. "
        "Ekip içi şeffaflık zayıf; bazı bilgileri paylaşmaktan kaçındı. "
        "Risk sinyali orta düzeyde, dikkat edilmeli.",

        "Bu hafta iletişim kalitesi düştü. Kriz anında çözüm odaklı değil tepki odaklı davrandı. "
        "Code review katılımı var ama derinliği yok. Ekip güvenine katkısı azalıyor. "
        "Destek ve mentorluk faydalı olabilir.",

        "Ekip içi iletişimde gerginlik yaşandı. Bilgiyi saklamak gibi bir tutum sergiledi. "
        "Code review süreçlerine katılımı azaldı. İş birliği kalitesi düşüyor; "
        "erken müdahale sinyali var.",
    ],
    ("medium_risk", 4, "sw"): [
        "Gelişim isteği var ama tutarsız. Bu hafta yeni bir şey öğrenmek yerine rutin işlere odaklandı. "
        "Dökümantasyon disiplini zayıf. Kariyer belirsizliği var; yönlendirmeye ihtiyaç duyuyor. "
        "Durgunluk başlangıcı olarak değerlendirilebilir.",

        "Bu hafta öğrenme faaliyeti sıfırdı. Dökümantasyon görevlerini erteledi. "
        "Kariyer hedefleri hakkında soru sorduğumda belirsiz cevaplar aldım. "
        "Sahiplenme duygusu zayıflıyor, destek ve yönlendirme gerekiyor.",

        "Gelişim sahiplenme sinyali azaldı. Yeni yaklaşımlara direnç başladı. "
        "Dökümantasyon eksik. Kariyer belirsizliği tükenmişlik riskini artırabilir; "
        "görüşme planlanmalı.",
    ],
}

# Satış için de kısa bir mapping — mevcut satış verisini tamamlar
SA_TEXTS = {
    ("high", 1, "sa"): [
        "Bu hafta pipeline yönetiminde mükemmel bir disiplin sergiledi. "
        "CRM kayıtları güncel ve eksiksizdi. Müşteri takip disiplini çok yüksek, "
        "itiraz yönetiminde sakin ve çözüm odaklı bir yaklaşım benimsedi. "
        "Ekip hedefleri konusunda istekli ve hevesli.",

        "Lead dönüşüm kalitesi bu hafta da yüksekti. Pipeline'ını düzenli güncelliyor, "
        "hiçbir müşteri takibi aksatmadı. Hedef kapama disiplini örnek gösterilebilir. "
        "Tükenmişlik ya da kopma sinyali hiç gözlemlemedim.",
    ],
    ("high", 2, "sa"): [
        "Motivasyonu ve satış enerjisi çok yüksekti. Zor müşteri görüşmelerinde bile istekli ve sabırlı kaldı. "
        "Ekip hedeflerine olan bağlılığı ve aidiyet hissi çok güçlü. "
        "Psikolojik güven açısından ekibe olumlu enerji katıyor.",

        "Bu hafta yüksek enerji ve motivasyonla çalıştı. Başarısız kapanışlara rağmen motivasyonunu kaybetmedi. "
        "Ekip atmosferini olumlu etkiliyor; hedeflere olan inancı sağlam.",
    ],
    ("high", 3, "sa"): [
        "Ekip içi bilgi paylaşımı ve iletişim kalitesi bu hafta da mükemmeldi. "
        "Bir müşteri itirazını hem çözdü hem de tekniği ekiple paylaştı. "
        "Şeffaf ve destekleyici tutumu ekip uyumunu güçlendiriyor.",

        "Kriz anında sakinliğini korudu ve çözüm odaklı davrandı. "
        "Ekip içinde bilgi saklamıyor; başarılı müşteri görüşmelerini herkesle paylaşıyor. "
        "CRM disiplini mükemmel.",
    ],
    ("high", 4, "sa"): [
        "Satış tekniklerini geliştirmeye devam ediyor; bu hafta yeni bir kapatma yöntemi denedi ve başarıyla uyguladı. "
        "Uzun vadeli kariyer planı net, şirkette büyüme motivasyonu yüksek. "
        "Lead dönüşüm kalitesi artıyor.",

        "Gelişim sahiplenme sinyali çok güçlü. Yeni satış yaklaşımlarını kendi inisiyatifiyle öğreniyor. "
        "Kariyer hedefleri net ve şirketle örtüşüyor.",
    ],
    ("atrisk", 1, "sa"): [
        "Bu hafta pipeline yönetimi çok kötüydü. CRM kayıtları güncel değildi, "
        "müşteri takipleri aksadı. Hedef kapama disiplini neredeyse yok. "
        "Motivasyon düşüşü ve tükenmişlik belirtileri çok net. İşten ayrılmayı düşündüğünü ima etti.",

        "Pipeline'ı başıboş bıraktı. Müşteri takibi yapmadı, itirazları yönetemedi. "
        "CRM hijyeni çok kötü. Ayrılma sinyali net; 'bu işe devam edemeyeceğim' dedi.",
    ],
    ("atrisk", 2, "sa"): [
        "Motivasyonu tamamen çökmüş durumda. Müşteri görüşmelerine isteksiz giriyor. "
        "Ekip hedeflerine olan inancını yitirmiş. Tükenmişlik çok belirgin; "
        "ayrılma niyetini doğrudan ifade etti.",

        "Bu hafta enerji sıfırın altında gibiydi. Toplantılarda yok gibi oturdu. "
        "Aidiyet hissi kalmamış; 'burada ne işim var' dedi. Acil destek gerekiyor.",
    ],
    ("atrisk", 3, "sa"): [
        "Ekip içi iletişim tamamen koptu. Bilgiyi saklamakla kalmadı, yanlış bilgi de verdi. "
        "Kriz anında geri çekildi, ekibi yalnız bıraktı. Güven ortamını zedeliyor.",

        "İletişim kalitesi dibe vurdu. Code review yoktu (satış CRM kaydı paylaşmadı). "
        "Ekipten kopuk ve pasif. Ayrılma kararını zaten vermiş gibi davranıyor.",
    ],
    ("atrisk", 4, "sa"): [
        "Gelişim isteği tamamen yok. Eğitim fırsatlarını reddetti. "
        "Kariyer belirsizliği değil kariyere ilgisizlik var. Durgunluk sinyali çok güçlü.",

        "Bu hafta hiçbir gelişim adımı atmadı. Kariyer hedefleri sorulduğunda 'fark etmez' dedi. "
        "Sahiplenme duygusu kalmamış.",
    ],
    ("medium", 1, "sa"): [
        "Pipeline yönetimi orta düzeyde. CRM kayıtları çoğunlukla güncel ama bazen eksik kalıyor. "
        "Müşteri takibi genel olarak iyi ama bazı fırsatlar kaçıyor. "
        "Motivasyon stabil; ciddi risk sinyali yok.",

        "Bu hafta takip disiplini yeterliydi. CRM'de bazı eksikler vardı ama hemen düzeltti. "
        "İtiraz yönetimi geliştirilebilir. Genel gidişat makul.",
    ],
    ("medium", 2, "sa"): [
        "Motivasyon dengeli. Yoğun müşteri temasında enerji düşüşü yaşadı ama toparladı. "
        "Ekip hedeflerine bağlılık makul; psikolojik güven stabil. Net risk sinyali yok.",

        "Bu hafta enerji biraz düşüktü ama performans etkilenmedi. "
        "Aidiyet hissi var, ekipten kopmaya dair sinyal gözlemlemedim.",
    ],
    ("medium", 3, "sa"): [
        "Ekip içi iletişim yeterli ama bilgi paylaşımı proaktif değil. "
        "Kriz anında sakin kaldı, çözüm odaklı davrandı. İletişim kalitesi orta düzeyde.",

        "Bu hafta iletişim kalitesi makul. Zorlu müşteri itirazında desteğe ihtiyaç duydu. "
        "Şeffaflık biraz artırılabilir.",
    ],
    ("medium", 4, "sa"): [
        "Gelişim isteği var ama uygulama yavaş. Yeni satış tekniklerini denemekten çekinmiyor. "
        "Kariyer planı belirsiz ama ayrılma sinyali yok.",

        "Bu hafta satış tekniklerini biraz geliştirdi. Daha fazla deneme yapmasını desteklemek lazım. "
        "Kariyer hedeflerine daha fazla odaklanmasına yardımcı olmak faydalı olur.",
    ],
    ("medium_risk", 1, "sa"): [
        "Pipeline yönetimi zayıf; bazı fırsatlar kaçtı. CRM kayıtları güncel değildi. "
        "Takip disiplini düşük, stres altında performans olumsuz etkileniyor. "
        "Risk sinyali orta düzeyde.",

        "Bu hafta hedef kapama disiplini düştü. CRM eksikleri var. "
        "Motivasyon dalgalanması fark edildi; destek gerekiyor.",
    ],
    ("medium_risk", 2, "sa"): [
        "Motivasyon dalgalı. Stres altında enerjisi düşüyor. "
        "Ayrılma niyeti net değil ama yorgunluk belirgin. Destek faydalı.",

        "Bu hafta enerji seviyesi istikrarsızdı. Psikolojik güven zayıflıyor gibi. "
        "Burnout başlangıcı olabilir; takip edilmeli.",
    ],
    ("medium_risk", 3, "sa"): [
        "İletişim kalitesi düştü. Kriz anında gergin tepkiler verdi. "
        "Ekip içi bilgi paylaşımı azaldı. Destek gerekiyor.",

        "Bu hafta iletişimde gerilim yaşandı. Şeffaflık zayıfladı. "
        "Ekip güvenine katkısı azalıyor.",
    ],
    ("medium_risk", 4, "sa"): [
        "Gelişim disiplini tutarsız. Kariyer belirsizliği var. "
        "Daha fazla mentorluk desteğine ihtiyaç duyuyor.",

        "Bu hafta öğrenme inisiyatifi düşüktü. Kariyer planı belirsiz; yönlendirme gerekiyor.",
    ],
}

# Tüm metinleri birleştir
ALL_TEXTS = {**SW_TEXTS, **SA_TEXTS}


def get_texts(profile, week, dept_code):
    key = (profile, week, dept_code)
    if key in ALL_TEXTS:
        return ALL_TEXTS[key]
    # Fallback: medium
    fallback = (("medium", week, dept_code))
    return ALL_TEXTS.get(fallback, ["Bu hafta çalışanın performansı gözlemlendi."])


def rand_float(lo, hi):
    return round(random.uniform(lo, hi), 3)


def nlp_from_profile(p_key):
    p = PROFILES[p_key]
    sl, s_lo, s_hi = p["sentiment"]
    return dict(
        sentiment_label=sl,
        sentiment_score=rand_float(s_lo, s_hi),
        motivation_score=rand_float(s_lo, s_hi),
        burnout_risk=p["burnout"],
        flight_risk=p["flight"],
        psychological_safety_score=rand_float(*p["psych"]),
        collaboration_score=rand_float(*p["collab"]),
        growth_signal_score=rand_float(*p["growth"]),
        leadership_support_score=rand_float(*p["leadership"]),
    )


def strengths_flags(p_key):
    if p_key == "high":
        return (
            ["güçlü teknik liderlik", "yüksek test disiplini", "proaktif iletişim"],
            [],
            [],
        )
    elif p_key == "medium":
        return (
            ["stabil performans", "ekip uyumu"],
            ["inisiyatif eksikliği"],
            ["gelişim mentorlugu"],
        )
    elif p_key == "medium_risk":
        return (
            ["temel yetkinlikler mevcut"],
            ["motivasyon dalgalanması", "stres yönetimi zayıf"],
            ["yakın takip", "birebir görüşme"],
        )
    else:  # atrisk
        return (
            [],
            ["tükenmişlik riski", "ayrılma sinyali", "bağlılık kaybı"],
            ["acil görüşme", "iş yükü azaltma", "kariyer yönlendirmesi"],
        )


def manager_summary(p_key, emp_code):
    summaries = {
        "high": f"{emp_code} bu dönemde güçlü performans sergiledi; teknik katkıları ve ekip uyumu çok olumlu.",
        "medium": f"{emp_code} makul performans gösterdi; gelişim desteği ve mentorluk faydalı olacak.",
        "medium_risk": f"{emp_code} için risk sinyalleri izlenmeli; motivasyon düşüşü ve stres yönetimi destek gerektiriyor.",
        "atrisk": f"{emp_code} için acil müdahale öneriliyor; tükenmişlik ve ayrılma riski yüksek.",
    }
    return summaries.get(p_key, "Çalışan değerlendirme dönemi tamamlandı.")


def recommended_action(p_key):
    actions = {
        "high": "Mevcut motivasyonu koruyun, liderlik fırsatları sunun.",
        "medium": "Gelişim planı yapın, mentorluk desteği sağlayın.",
        "medium_risk": "Birebir görüşme planlayın, iş yükünü gözden geçirin.",
        "atrisk": "Acil görüşme yapın, tükenmişlik nedenlerini tespit edin ve aksiyon alın.",
    }
    return actions.get(p_key, "Çalışanı yakından takip edin.")


def build_profile_from_analyses(analyses, emp_id, dept_id, period):
    if not analyses:
        return None
    year, month, week = period
    avg = lambda field: round(
        sum(getattr(a, field) or 0 for a in analyses) / len(analyses), 3
    )
    sentiments = [a.sentiment_label for a in analyses]
    burnouts   = [a.burnout_risk for a in analyses]
    flights    = [a.flight_risk for a in analyses]

    def dominant(lst):
        from collections import Counter
        c = Counter(lst)
        return c.most_common(1)[0][0]

    return dict(
        employee_id=emp_id,
        department_id=dept_id,
        period_type=NLPPeriodType.weekly,
        period_year=year,
        period_month=month,
        period_week=week,
        feedback_count=len(analyses),
        avg_sentiment_score=avg("sentiment_score"),
        avg_motivation_score=avg("motivation_score"),
        avg_psychological_safety_score=avg("psychological_safety_score"),
        avg_collaboration_score=avg("collaboration_score"),
        avg_growth_signal_score=avg("growth_signal_score"),
        burnout_risk_level=dominant(burnouts),
        flight_risk_level=dominant(flights),
    )


# ── Ana seed fonksiyonu ──────────────────────────────────────────────────────
def seed_department(dept_id, dept_code, question_defs, profile_map):
    print(f"\n{'='*60}")
    print(f"Dept {dept_id} ({dept_code.upper()}) seeding...")

    employees = db.query(Employee).filter(Employee.department_id == dept_id).all()
    if not employees:
        print("  Çalışan bulunamadı, atlanıyor.")
        return

    emp_ids = [e.id for e in employees]
    emp_by_id = {e.id: e for e in employees}

    # Yönetici bul (ilk manager pozisyonlu)
    manager_emp = next(
        (e for e in employees if "manager" in (e.position or "").lower()), employees[0]
    )

    # Soru oluştur (model_provider="synthetic" ile işaretli olmayanları ekle)
    created_questions = {}  # (week, direction) -> FeedbackQuestion
    for (week, direction, category, text) in question_defs:
        existing = (
            db.query(FeedbackQuestion)
            .filter(
                FeedbackQuestion.department_id == dept_id,
                FeedbackQuestion.week_number == week,
                FeedbackQuestion.direction == direction,
                FeedbackQuestion.category == category,
            )
            .first()
        )
        if existing:
            created_questions[(week, direction)] = existing
        else:
            q = FeedbackQuestion(
                week_number=week,
                direction=direction,
                question_text=text,
                category=category,
                department_id=dept_id,
                is_ai_generated=False,
            )
            db.add(q)
            db.flush()
            created_questions[(week, direction)] = q
            print(f"  + Soru eklendi: hafta={week} yön={direction.value} kategori={category}")

    db.commit()

    # Her dönem × çalışan için seed
    total_responses = 0
    total_nlp = 0
    total_profiles = 0

    for period in PERIODS:
        year, month, week = period
        theme_week = week  # 1-4

        # Bu dönem için soru yönleri
        peer_q = created_questions.get((theme_week, FeedbackDirection.peer_to_peer))
        mgr_to_emp_q = created_questions.get((theme_week, FeedbackDirection.manager_to_employee))
        emp_to_mgr_q = created_questions.get((theme_week, FeedbackDirection.employee_to_manager))

        # Fallback: başka haftalardaki sorular
        if not peer_q:
            peer_q = next(
                (v for k, v in created_questions.items() if k[1] == FeedbackDirection.peer_to_peer),
                None,
            )

        for target_emp in employees:
            # Bu çalışan zaten bu dönemde response almış mı?
            existing_resp = (
                db.query(FeedbackResponse)
                .filter(
                    FeedbackResponse.receiver_id == target_emp.id,
                    FeedbackResponse.period_year == year,
                    FeedbackResponse.period_month == month,
                    FeedbackResponse.period_week == week,
                )
                .count()
            )
            if existing_resp >= 2:
                continue

            profile_key = profile_map.get(target_emp.id, "medium")
            p = PROFILES[profile_key]
            score_lo, score_hi = p["scores"]
            texts = get_texts(profile_key, theme_week, dept_code)

            is_manager = target_emp.id == manager_emp.id

            # Peer-to-peer: diğer çalışanlardan feedback
            senders = [e for e in employees if e.id != target_emp.id]
            random.shuffle(senders)
            peer_senders = senders[:3]

            q = peer_q or list(created_questions.values())[0]

            for i, sender in enumerate(peer_senders):
                text = texts[i % len(texts)]
                score = random.randint(score_lo, score_hi)

                resp = FeedbackResponse(
                    sender_id=sender.id,
                    receiver_id=target_emp.id,
                    question_id=q.id,
                    response_text=text,
                    score_communication=score,
                    score_teamwork=max(1, score + random.randint(-1, 1)),
                    score_leadership=max(1, score + random.randint(-1, 1)),
                    score_technical=max(1, score + random.randint(-1, 1)),
                    period_week=week,
                    period_month=month,
                    period_year=year,
                )
                db.add(resp)
                db.flush()
                total_responses += 1

                # NLP Analizi
                nlp_vals = nlp_from_profile(profile_key)
                strengths, flags, needs = strengths_flags(profile_key)
                code = target_emp.external_employee_code or f"EMP-{target_emp.id}"
                nlp = FeedbackNLPAnalysis(
                    source_type=NLPSourceType.weekly_feedback,
                    weekly_feedback_id=resp.id,
                    employee_id=target_emp.id,
                    reviewer_employee_id=sender.id,
                    department_id=dept_id,
                    direction=q.direction.value if hasattr(q.direction, "value") else str(q.direction),
                    theme=q.category,
                    analysis_version="v1",
                    model_provider="synthetic_seed_360",
                    model_name="rule_based_v1",
                    key_strengths=strengths,
                    risk_flags=flags,
                    support_needs=needs,
                    keywords=strengths[:2] + flags[:2],
                    manager_summary=manager_summary(profile_key, code),
                    **nlp_vals,
                )
                db.add(nlp)
                db.flush()
                total_nlp += 1

            # Yönetici → çalışan (yönetici değilse)
            if not is_manager and mgr_to_emp_q:
                mgr_text = get_texts(profile_key, theme_week, dept_code)
                text = mgr_text[0]
                score = random.randint(score_lo, score_hi)
                resp = FeedbackResponse(
                    sender_id=manager_emp.id,
                    receiver_id=target_emp.id,
                    question_id=mgr_to_emp_q.id,
                    response_text=text,
                    score_communication=score,
                    score_teamwork=max(1, score + random.randint(-1, 1)),
                    score_leadership=max(1, score + random.randint(-1, 1)),
                    score_technical=max(1, score + random.randint(-1, 1)),
                    period_week=week,
                    period_month=month,
                    period_year=year,
                )
                db.add(resp)
                db.flush()
                total_responses += 1

                nlp_vals = nlp_from_profile(profile_key)
                strengths, flags, needs = strengths_flags(profile_key)
                code = target_emp.external_employee_code or f"EMP-{target_emp.id}"
                nlp = FeedbackNLPAnalysis(
                    source_type=NLPSourceType.weekly_feedback,
                    weekly_feedback_id=resp.id,
                    employee_id=target_emp.id,
                    reviewer_employee_id=manager_emp.id,
                    department_id=dept_id,
                    direction=(mgr_to_emp_q.direction.value
                               if hasattr(mgr_to_emp_q.direction, "value")
                               else str(mgr_to_emp_q.direction)),
                    theme=mgr_to_emp_q.category,
                    analysis_version="v1",
                    model_provider="synthetic_seed_360",
                    model_name="rule_based_v1",
                    key_strengths=strengths,
                    risk_flags=flags,
                    support_needs=needs,
                    keywords=strengths[:2] + flags[:2],
                    manager_summary=manager_summary(profile_key, code),
                    **nlp_vals,
                )
                db.add(nlp)
                db.flush()
                total_nlp += 1

            # Çalışan → yönetici
            if not is_manager and emp_to_mgr_q:
                mgr_profile = profile_map.get(manager_emp.id, "high")
                mgr_texts = get_texts(mgr_profile, theme_week, dept_code)
                score = random.randint(score_lo, score_hi)
                resp = FeedbackResponse(
                    sender_id=target_emp.id,
                    receiver_id=manager_emp.id,
                    question_id=emp_to_mgr_q.id,
                    response_text=mgr_texts[0],
                    score_communication=score,
                    score_teamwork=max(1, score + random.randint(-1, 1)),
                    score_leadership=max(1, score + random.randint(-1, 1)),
                    score_technical=max(1, score + random.randint(-1, 1)),
                    period_week=week,
                    period_month=month,
                    period_year=year,
                )
                db.add(resp)
                db.flush()
                total_responses += 1

                nlp_vals = nlp_from_profile(mgr_profile)
                strengths, flags, needs = strengths_flags(mgr_profile)
                code = manager_emp.external_employee_code or f"MGR-{manager_emp.id}"
                nlp = FeedbackNLPAnalysis(
                    source_type=NLPSourceType.weekly_feedback,
                    weekly_feedback_id=resp.id,
                    employee_id=manager_emp.id,
                    reviewer_employee_id=target_emp.id,
                    department_id=dept_id,
                    direction=(emp_to_mgr_q.direction.value
                               if hasattr(emp_to_mgr_q.direction, "value")
                               else str(emp_to_mgr_q.direction)),
                    theme=emp_to_mgr_q.category,
                    analysis_version="v1",
                    model_provider="synthetic_seed_360",
                    model_name="rule_based_v1",
                    key_strengths=strengths,
                    risk_flags=flags,
                    support_needs=needs,
                    keywords=strengths[:2] + flags[:2],
                    manager_summary=manager_summary(mgr_profile, code),
                    **nlp_vals,
                )
                db.add(nlp)
                db.flush()
                total_nlp += 1

        db.commit()

    # ── EmployeeNLPProfile oluştur ───────────────────────────────────────────
    for period in PERIODS:
        year, month, week = period
        for emp in employees:
            # Zaten var mı?
            existing_prof = (
                db.query(EmployeeNLPProfile)
                .filter(
                    EmployeeNLPProfile.employee_id == emp.id,
                    EmployeeNLPProfile.period_type == NLPPeriodType.weekly,
                    EmployeeNLPProfile.period_year == year,
                    EmployeeNLPProfile.period_month == month,
                    EmployeeNLPProfile.period_week == week,
                )
                .first()
            )
            if existing_prof:
                continue

            analyses = (
                db.query(FeedbackNLPAnalysis)
                .join(FeedbackResponse, FeedbackNLPAnalysis.weekly_feedback_id == FeedbackResponse.id)
                .filter(
                    FeedbackNLPAnalysis.employee_id == emp.id,
                    FeedbackNLPAnalysis.source_type == NLPSourceType.weekly_feedback,
                    FeedbackResponse.period_year == year,
                    FeedbackResponse.period_month == month,
                    FeedbackResponse.period_week == week,
                )
                .all()
            )

            if not analyses:
                continue

            profile_key = profile_map.get(emp.id, "medium")
            strengths, flags, needs = strengths_flags(profile_key)
            code = emp.external_employee_code or f"EMP-{emp.id}"

            profile_data = build_profile_from_analyses(analyses, emp.id, dept_id, period)
            if not profile_data:
                continue

            prof = EmployeeNLPProfile(
                **profile_data,
                top_strengths=strengths,
                top_risk_areas=flags,
                top_support_needs=needs,
                manager_summary=manager_summary(profile_key, code),
                recommended_action=recommended_action(profile_key),
            )
            db.add(prof)
            total_profiles += 1

        db.commit()

    print(f"  ✓ {total_responses} FeedbackResponse, {total_nlp} NLPAnalysis, {total_profiles} NLPProfile eklendi.")


# ── Satış profil haritası ────────────────────────────────────────────────────
def build_satis_profiles(dept_id):
    employees = db.query(Employee).filter(Employee.department_id == dept_id).all()
    mapping = {}
    for i, emp in enumerate(employees):
        code = emp.external_employee_code or ""
        pos  = (emp.position or "").lower()
        if "manager" in pos:
            mapping[emp.id] = "high"
        elif i % 3 == 0:
            mapping[emp.id] = "atrisk"
        elif i % 4 == 1:
            mapping[emp.id] = "medium_risk"
        else:
            mapping[emp.id] = "medium" if i % 2 == 0 else "high"
    return mapping


# ── RESET ────────────────────────────────────────────────────────────────────
if RESET:
    print("RESET: Mevcut synthetic_seed_360 verileri siliniyor...")
    # NLP analizleri
    db.query(FeedbackNLPAnalysis).filter(
        FeedbackNLPAnalysis.model_provider == "synthetic_seed_360"
    ).delete(synchronize_session=False)
    db.commit()

    # Response'ları bul (yazılım dept için)
    sw_emp_ids = [e.id for e in db.query(Employee).filter(Employee.department_id == YAZILIM_DEPT_ID).all()]
    db.query(FeedbackResponse).filter(
        FeedbackResponse.receiver_id.in_(sw_emp_ids)
    ).delete(synchronize_session=False)
    db.commit()

    # Profilleri sil (yazılım)
    db.query(EmployeeNLPProfile).filter(
        EmployeeNLPProfile.employee_id.in_(sw_emp_ids)
    ).delete(synchronize_session=False)
    db.commit()
    print("  RESET tamamlandı.")


# ── Çalıştır ─────────────────────────────────────────────────────────────────
random.seed(42)

seed_department(
    YAZILIM_DEPT_ID, "sw",
    YAZILIM_QUESTIONS,
    YAZILIM_PROFILES,
)

satis_profiles = build_satis_profiles(SATIS_DEPT_ID)
seed_department(
    SATIS_DEPT_ID, "sa",
    SATIS_QUESTIONS,
    satis_profiles,
)

print("\n✅ Tüm seed tamamlandı.")

# Özet
from app.db.models.nlp import FeedbackNLPAnalysis as FNLPA, EmployeeNLPProfile as ENLPP
from app.db.models.feedback import FeedbackResponse as FR

print(f"  Toplam FeedbackResponse : {db.query(FR).count()}")
print(f"  Toplam FeedbackNLPAnalysis: {db.query(FNLPA).count()}")
print(f"  Toplam EmployeeNLPProfile : {db.query(ENLPP).count()}")
