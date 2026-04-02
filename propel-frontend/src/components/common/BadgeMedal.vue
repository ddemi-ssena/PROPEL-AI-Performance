<template>
  <div class="inline-flex items-center gap-3" :title="description || label">
    <div class="relative shrink-0" :class="sizeClass">
      <div class="absolute inset-[-10%] z-0 rounded-full opacity-95" :class="petalClass" />
      <div class="absolute inset-x-[16%] -bottom-[24%] z-0 flex justify-between">
        <span
          class="block w-[31%] rounded-b-[10px] border-b border-white/30 shadow-[inset_0_1px_0_rgba(255,255,255,0.35),0_10px_16px_rgba(15,23,42,0.20)]"
          :class="ribbonLeftClass"
          :style="{ height: ribbonHeight }"
        />
        <span
          class="block w-[31%] rounded-b-[10px] border-b border-white/30 shadow-[inset_0_1px_0_rgba(255,255,255,0.35),0_10px_16px_rgba(15,23,42,0.20)]"
          :class="ribbonRightClass"
          :style="{ height: ribbonHeight }"
        />
      </div>

      <div class="absolute inset-[2%] rounded-full opacity-90 blur-[2.5px]" :class="glowClass" />
      <div class="absolute inset-0 rounded-full border shadow-[0_18px_30px_rgba(15,23,42,0.22)]" :class="frameClass" />

      <div
        class="relative z-10 flex h-full w-full items-center justify-center rounded-full border shadow-[0_18px_34px_rgba(15,23,42,0.24),inset_0_2px_0_rgba(255,255,255,0.82),inset_0_-10px_16px_rgba(15,23,42,0.18)]"
        :class="outerClass"
      >
        <div class="absolute inset-[8%] rounded-full bg-white/15 blur-[2px]" />
        <div class="absolute left-[14%] right-[14%] top-[9%] h-[20%] rounded-full bg-white/70 blur-[1px]" />
        <div class="absolute inset-[10%] rounded-full border border-white/18" />
        <div
          class="relative z-10 flex h-[64%] w-[64%] items-center justify-center rounded-full border text-[0.56em] font-black tracking-[0.18em] shadow-[inset_0_2px_0_rgba(255,255,255,0.50),inset_0_-5px_8px_rgba(15,23,42,0.16)]"
          :class="innerClass"
        >
          <div class="absolute inset-[10%] rounded-full border border-white/18" />
          {{ initials }}
        </div>
      </div>
    </div>

    <div v-if="showLabel" class="min-w-0">
      <p class="truncate text-xs font-semibold text-slate-900">{{ label }}</p>
      <p v-if="description" class="truncate text-[11px] text-slate-600">{{ description }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { BadgeLevel, BadgeType } from '@/services/api/feedback.api'

const props = withDefaults(defineProps<{
  badgeType: BadgeType
  badgeLevel?: BadgeLevel
  showLabel?: boolean
  size?: 'xs' | 'sm' | 'md'
  description?: string
}>(), {
  badgeLevel: 'bronze',
  showLabel: false,
  size: 'sm',
  description: '',
})

const badgeMeta: Record<BadgeType, { label: string; initials: string; palette: keyof typeof paletteStyles }> = {
  communicator: { label: 'Quality Gatekeeper', initials: 'QG', palette: 'silver' },
  reliable: { label: 'Legacy Hunter', initials: 'LH', palette: 'bronze' },
  team_player: { label: 'Team Catalyst', initials: 'TC', palette: 'gold' },
  problem_solver: { label: 'Block Buster', initials: 'BB', palette: 'roseMetal' },
  mentor: { label: 'Knowledge Lighthouse', initials: 'KL', palette: 'violetMetal' },
  innovator: { label: 'Agile Mindset', initials: 'AM', palette: 'pinkMetal' },
  speed_champion: { label: 'Hiz Sampiyonu', initials: 'HS', palette: 'steelBlue' },
}

const paletteStyles = {
  gold: {
    petal: 'bg-[radial-gradient(circle_at_center,transparent_57%,rgba(245,158,11,0.14)_58%,rgba(245,158,11,0.14)_64%,transparent_65%),conic-gradient(from_0deg,#fff7cc_0deg,#fcd34d_36deg,#fde68a_72deg,#f59e0b_108deg,#fde68a_144deg,#fcd34d_180deg,#fff7cc_216deg,#f59e0b_252deg,#fde68a_288deg,#fcd34d_324deg,#fff7cc_360deg)]',
    frame: 'border-yellow-200/80',
    outer: 'border-yellow-100 bg-[radial-gradient(circle_at_30%_22%,#fffef7_0%,#fef3c7_18%,#fcd34d_38%,#f59e0b_72%,#a16207_100%)]',
    inner: 'border-yellow-100 bg-[radial-gradient(circle_at_30%_22%,#fffef8_0%,#fde68a_26%,#facc15_68%,#ca8a04_100%)] text-amber-950',
    ribbonLeft: 'bg-[linear-gradient(180deg,#1d4ed8_0%,#1e3a8a_100%)]',
    ribbonRight: 'bg-[linear-gradient(180deg,#38bdf8_0%,#0369a1_100%)]',
    glow: 'bg-yellow-200/60',
  },
  silver: {
    petal: 'bg-[radial-gradient(circle_at_center,transparent_57%,rgba(148,163,184,0.14)_58%,rgba(148,163,184,0.14)_64%,transparent_65%),conic-gradient(from_0deg,#ffffff_0deg,#cbd5e1_36deg,#e2e8f0_72deg,#94a3b8_108deg,#e2e8f0_144deg,#cbd5e1_180deg,#ffffff_216deg,#94a3b8_252deg,#e2e8f0_288deg,#cbd5e1_324deg,#ffffff_360deg)]',
    frame: 'border-slate-300/90',
    outer: 'border-slate-200 bg-[radial-gradient(circle_at_30%_22%,#ffffff_0%,#f8fafc_18%,#e2e8f0_38%,#94a3b8_72%,#475569_100%)]',
    inner: 'border-slate-200 bg-[radial-gradient(circle_at_30%_22%,#ffffff_0%,#f8fafc_24%,#cbd5e1_68%,#64748b_100%)] text-slate-700',
    ribbonLeft: 'bg-[linear-gradient(180deg,#334155_0%,#0f172a_100%)]',
    ribbonRight: 'bg-[linear-gradient(180deg,#94a3b8_0%,#475569_100%)]',
    glow: 'bg-slate-200/55',
  },
  bronze: {
    petal: 'bg-[radial-gradient(circle_at_center,transparent_57%,rgba(194,65,12,0.14)_58%,rgba(194,65,12,0.14)_64%,transparent_65%),conic-gradient(from_0deg,#ffedd5_0deg,#fb923c_36deg,#fdba74_72deg,#c2410c_108deg,#fdba74_144deg,#fb923c_180deg,#ffedd5_216deg,#9a3412_252deg,#fdba74_288deg,#fb923c_324deg,#ffedd5_360deg)]',
    frame: 'border-orange-200/85',
    outer: 'border-orange-100 bg-[radial-gradient(circle_at_30%_22%,#fff7ed_0%,#fed7aa_18%,#fb923c_38%,#c2410c_72%,#7c2d12_100%)]',
    inner: 'border-orange-100 bg-[radial-gradient(circle_at_30%_22%,#fff7ed_0%,#fdba74_24%,#ea580c_68%,#9a3412_100%)] text-orange-950',
    ribbonLeft: 'bg-[linear-gradient(180deg,#7c3aed_0%,#4c1d95_100%)]',
    ribbonRight: 'bg-[linear-gradient(180deg,#f97316_0%,#c2410c_100%)]',
    glow: 'bg-orange-200/55',
  },
  roseMetal: {
    petal: 'bg-[radial-gradient(circle_at_center,transparent_57%,rgba(244,63,94,0.14)_58%,rgba(244,63,94,0.14)_64%,transparent_65%),conic-gradient(from_0deg,#fff1f2_0deg,#fb7185_36deg,#fda4af_72deg,#be185d_108deg,#fda4af_144deg,#fb7185_180deg,#fff1f2_216deg,#9f1239_252deg,#fda4af_288deg,#fb7185_324deg,#fff1f2_360deg)]',
    frame: 'border-rose-200/85',
    outer: 'border-rose-100 bg-[radial-gradient(circle_at_30%_22%,#fff7f8_0%,#fecdd3_18%,#fb7185_38%,#be185d_72%,#831843_100%)]',
    inner: 'border-rose-100 bg-[radial-gradient(circle_at_30%_22%,#fff1f2_0%,#fda4af_24%,#f43f5e_68%,#9f1239_100%)] text-rose-950',
    ribbonLeft: 'bg-[linear-gradient(180deg,#be123c_0%,#881337_100%)]',
    ribbonRight: 'bg-[linear-gradient(180deg,#fb7185_0%,#be185d_100%)]',
    glow: 'bg-rose-200/55',
  },
  violetMetal: {
    petal: 'bg-[radial-gradient(circle_at_center,transparent_57%,rgba(139,92,246,0.14)_58%,rgba(139,92,246,0.14)_64%,transparent_65%),conic-gradient(from_0deg,#f5f3ff_0deg,#a78bfa_36deg,#ddd6fe_72deg,#7c3aed_108deg,#ddd6fe_144deg,#a78bfa_180deg,#f5f3ff_216deg,#5b21b6_252deg,#ddd6fe_288deg,#a78bfa_324deg,#f5f3ff_360deg)]',
    frame: 'border-violet-200/85',
    outer: 'border-violet-100 bg-[radial-gradient(circle_at_30%_22%,#faf5ff_0%,#e9d5ff_18%,#a78bfa_38%,#7c3aed_72%,#4c1d95_100%)]',
    inner: 'border-violet-100 bg-[radial-gradient(circle_at_30%_22%,#f5f3ff_0%,#ddd6fe_24%,#8b5cf6_68%,#5b21b6_100%)] text-violet-950',
    ribbonLeft: 'bg-[linear-gradient(180deg,#6d28d9_0%,#3b0764_100%)]',
    ribbonRight: 'bg-[linear-gradient(180deg,#c084fc_0%,#7c3aed_100%)]',
    glow: 'bg-violet-200/55',
  },
  pinkMetal: {
    petal: 'bg-[radial-gradient(circle_at_center,transparent_57%,rgba(232,121,249,0.14)_58%,rgba(232,121,249,0.14)_64%,transparent_65%),conic-gradient(from_0deg,#fdf4ff_0deg,#f472b6_36deg,#f0abfc_72deg,#c026d3_108deg,#f0abfc_144deg,#f472b6_180deg,#fdf4ff_216deg,#a21caf_252deg,#f0abfc_288deg,#f472b6_324deg,#fdf4ff_360deg)]',
    frame: 'border-fuchsia-200/85',
    outer: 'border-fuchsia-100 bg-[radial-gradient(circle_at_30%_22%,#fdf4ff_0%,#f5d0fe_18%,#f472b6_38%,#c026d3_72%,#701a75_100%)]',
    inner: 'border-fuchsia-100 bg-[radial-gradient(circle_at_30%_22%,#fdf4ff_0%,#f0abfc_24%,#e879f9_68%,#a21caf_100%)] text-fuchsia-950',
    ribbonLeft: 'bg-[linear-gradient(180deg,#db2777_0%,#9d174d_100%)]',
    ribbonRight: 'bg-[linear-gradient(180deg,#f472b6_0%,#c026d3_100%)]',
    glow: 'bg-fuchsia-200/55',
  },
  steelBlue: {
    petal: 'bg-[radial-gradient(circle_at_center,transparent_57%,rgba(56,189,248,0.14)_58%,rgba(56,189,248,0.14)_64%,transparent_65%),conic-gradient(from_0deg,#f0f9ff_0deg,#7dd3fc_36deg,#bae6fd_72deg,#2563eb_108deg,#bae6fd_144deg,#7dd3fc_180deg,#f0f9ff_216deg,#1d4ed8_252deg,#bae6fd_288deg,#7dd3fc_324deg,#f0f9ff_360deg)]',
    frame: 'border-sky-200/85',
    outer: 'border-sky-100 bg-[radial-gradient(circle_at_30%_22%,#f0f9ff_0%,#dbeafe_18%,#7dd3fc_38%,#2563eb_72%,#1e3a8a_100%)]',
    inner: 'border-sky-100 bg-[radial-gradient(circle_at_30%_22%,#f0f9ff_0%,#bae6fd_24%,#38bdf8_68%,#1d4ed8_100%)] text-sky-950',
    ribbonLeft: 'bg-[linear-gradient(180deg,#1d4ed8_0%,#172554_100%)]',
    ribbonRight: 'bg-[linear-gradient(180deg,#60a5fa_0%,#2563eb_100%)]',
    glow: 'bg-sky-200/55',
  },
} as const

const levelRing = {
  bronze: 'ring-[3px] ring-orange-200/75',
  silver: 'ring-[3px] ring-slate-200/85',
  gold: 'ring-[3px] ring-yellow-300/85',
} as const

const sizeClass = computed(() => {
  const map = {
    xs: 'h-6 w-6 text-[9px]',
    sm: 'h-8 w-8 text-[11px]',
    md: 'h-10 w-10 text-[12px]',
  }
  return `${map[props.size]} ${levelRing[props.badgeLevel]} rounded-full`
})

const ribbonHeight = computed(() => {
  const map = {
    xs: '7px',
    sm: '9px',
    md: '11px',
  }
  return map[props.size]
})

const meta = computed(() => badgeMeta[props.badgeType] || badgeMeta.team_player)
const palette = computed(() => paletteStyles[meta.value.palette])
const label = computed(() => meta.value.label)
const initials = computed(() => meta.value.initials)
const petalClass = computed(() => palette.value.petal)
const frameClass = computed(() => palette.value.frame)
const outerClass = computed(() => palette.value.outer)
const innerClass = computed(() => palette.value.inner)
const ribbonLeftClass = computed(() => palette.value.ribbonLeft)
const ribbonRightClass = computed(() => palette.value.ribbonRight)
const glowClass = computed(() => palette.value.glow)
</script>
