import logging
from typing import Dict, Any

from app.core.config import settings

logger = logging.getLogger(__name__)

class MLPredictionEngine:
    def __init__(self):
        """
        Initialize the ML Prediction Engine.
        Loads the BERTürk sentiment analysis model.
        """
        self.sentiment_analyzer = None
        if not settings.ENABLE_LOCAL_SENTIMENT_MODEL:
            logger.info("Local sentiment model disabled; weekly pulse NLP will use neutral fallback scores.")
            return
        try:
            from transformers import pipeline
            logger.info("Yükleniyor: savasy/bert-base-turkish-sentiment-cased...")
            self.sentiment_analyzer = pipeline(
                "sentiment-analysis", 
                model="savasy/bert-base-turkish-sentiment-cased"
            )
            logger.info("BERTürk modeli başarıyla yüklendi.")
        except Exception as e:
            logger.error(f"Model yüklenirken hata oluştu: {e}")
            self.sentiment_analyzer = None

    def _get_sentiment_score(self, text: str) -> float:
        """
        Boş metinler için 0, positive için score, negative için -score döner.
        """
        if not text or len(text.strip()) < 3:
            return 0.0
            
        if self.sentiment_analyzer is None:
            # Model yüklenemediyse dummy değer
            return 0.0
            
        try:
            result = self.sentiment_analyzer(text[:512])[0]
            label = result['label']
            score = result['score']
            
            # savasy modeli genelde 'positive' ve 'negative' döner.
            if label.lower() == 'positive':
                return float(score)
            elif label.lower() == 'negative':
                return -float(score)
            else:
                return 0.0
        except Exception as e:
            logger.error(f"Duygu analizi hatası: {e}")
            return 0.0

    def analyze_pulse_survey(self, q4_diff: str, q5_succ: str, q6_sugg: str) -> Dict[str, float]:
        """
        Açık uçlu sorulardan (Zorluk, Başarı, Öneri) 
        MTE (Motivasyon Eğimi) ve ARS (Ayrılma Riski) hesaplar.
        
        MTE: -1.0 (Çok Negatif) ile +1.0 (Çok Pozitif) arası.
        ARS: 0.0 (Düşük Risk) ile 1.0 (Yüksek Risk) arası.
        """
        # 1. Metinlerin duygu skorlarını al
        diff_score = self._get_sentiment_score(q4_diff)  # Zorluk genelde negatiftir ama nasıl ifade edildiğine göre değişir
        succ_score = self._get_sentiment_score(q5_succ)  # Başarı genelde pozitiftir
        sugg_score = self._get_sentiment_score(q6_sugg)  # Öneri nötr veya yapıcı olabilir

        # MTE (Motivasyon Trend Eğimi)
        # Çok basit bir ağırlıklandırma: Başarı skorunu artır, Zorluktan etkilen, Öneri yapıcıysa pozitif etki
        total_sentiment = (diff_score * 0.4) + (succ_score * 0.5) + (sugg_score * 0.1)
        mte_score = max(-1.0, min(1.0, total_sentiment))
        
        # ARS (Ayrılma Riski)
        # Zorluk çok negatifse, ve genel duygu negatifse ayrılma riski artar.
        # Örneğin zorluk -0.9, başarı yok: total_sentiment = -0.36
        ars_score = 0.0
        if total_sentiment < 0:
            ars_score = abs(total_sentiment) # 0 ile 1 arası
            # Eğer adam zorluk çok negatif girmişse riski bir miktar daha artır
            if diff_score < -0.5:
                ars_score += 0.2
                
        ars_score = max(0.0, min(1.0, ars_score))

        return {
            "mte_score": round(mte_score, 3),
            "ars_score": round(ars_score, 3)
        }

# Singleton instance
prediction_engine = MLPredictionEngine()
