# Sprint 16 Diversity Audit Report

## Executive Summary

Date: 2026-06-14 16:05 | Provider: DeepSeek | Model: deepseek-chat

## Brief Propagation

| Brief | Marker | Segments | Avatars | Pains | Offers | Missions | HTML Size |
|-------|--------|----------|---------|-------|--------|----------|-----------|
| photo_studio | Аренда фотостудий в Москве. 7  | 3 | 5 | 0 | 10 | 0 | 0 |
| dental_clinic | Частная стоматология в СПб. 5  | 3 | 5 | 0 | 0 | 0 | 0 |
| b2b_service | Агентство B2B маркетинга. Лидо | 3 | 5 | 0 | 15 | 0 | 0 |

## Output Diversity

| Metric | photo_studio | dental_clinic | b2b_service |
|--------|-------------|---------------|-------------|
| segments_count | 3 | 3 | 3 |
| avatars_count | 5 | 5 | 5 |
| pains_count | 0 | 0 | 0 |
| offers_count | 10 | 0 | 15 |
| missions_count | 0 | 0 | 0 |

## Similarity Audit

- **photo_studio vs dental_clinic**: title_sim=0.00%, cta_sim=0.00%
- **photo_studio vs b2b_service**: title_sim=0.00%, cta_sim=0.00%
- **dental_clinic vs b2b_service**: title_sim=0.00%, cta_sim=0.00%

- **Title unique ratio:** 0.00%
- **CTA unique ratio:** 0.00%

## Schema Audit

- **photo_studio**: 2/5 schema passed
- **dental_clinic**: 4/5 schema passed
- **b2b_service**: 2/5 schema passed

## Final Verdict

- Pipeline Stability: PASS (all 3 niches completed)
- AI Diversity: FAIL (title_unique=0%, cta_unique=0%)
- Ready for next stage: NO