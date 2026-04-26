# 도메인 카드 — AI / 머신러닝 / LLM

> 공공입찰(나라장터) 대상 AI/ML 사업 제안서 작성 시 참조.

## 사업 유형 시그널 (RFP 키워드)
"AI 모델 개발", "머신러닝", "딥러닝", "자연어 처리(NLP)", "컴퓨터 비전(CV)",
"대규모 언어 모델(LLM)", "생성형 AI", "RAG", "MLOps", "AI 챗봇", "AI 에이전트",
"음성 인식(ASR/STT)", "음성 합성(TTS)", "객체 인식", "예측 모델",
"AI 학습 데이터", "데이터 라벨링", "AI 윤리", "AI 신뢰성"

## 정책·법제 연계
- **국가 AI 전략 (2030)** — 디지털플랫폼정부 핵심 동력
- **AI 기본법** (2024 제정) — AI 신뢰성·투명성·공정성 의무
- **EU AI Act 대응** — 고위험 AI 시스템 분류·평가
- **인공지능 신뢰성 기준** (TTA TTAK.KO-10.1407) — 한국형 AI 평가지표
- **개인정보보호위원회 AI 자율점검표** — 자동화된 의사결정 의무
- **K-디지털 기초학습** — 대국민 AI 리터러시
- **소버린 AI(Sovereign AI)** — 국산 AI 모델 활용 정책

## 표준 아키텍처
```
[데이터] → [학습] → [평가] → [배포] → [모니터링]
 라벨링    GPU 클러스터  벤치마크   Triton    드리프트 감지
 정제      PyTorch/TF   Eval Harness ONNX     성능 지표
 증강      MLflow       Holdout    KServe    재학습 파이프라인
                                   FastAPI    모델 거버넌스
                                   vLLM
```

핵심 스택:
- **프레임워크**: PyTorch, TensorFlow, JAX, Hugging Face Transformers
- **MLOps**: MLflow, Kubeflow, Airflow, Ray, Weights & Biases
- **모델 서빙**: NVIDIA Triton, TorchServe, KServe, BentoML, vLLM, TGI
- **LLM/RAG**: LangChain, LlamaIndex, Haystack, Vector DB(Milvus/Qdrant/Weaviate)
- **데이터**: Label Studio, CVAT, Snorkel, DVC
- **컴퓨팅**: NVIDIA DGX, A100/H100, AMD MI300, 국산 NPU(SAPEON, Rebellions, FuriosaAI)

## 기술 요구사항 체크리스트
- [ ] 학습 데이터 품질·다양성·편향 검증
- [ ] 모델 정확도·정밀도·재현율·F1 검증
- [ ] 모델 설명가능성(XAI) — SHAP, LIME
- [ ] 적대적 공격 대응 (Adversarial Robustness)
- [ ] 개인정보 비식별화 (Differential Privacy)
- [ ] 모델 재학습 파이프라인 (Continual Learning)
- [ ] A/B 테스트·카나리 배포
- [ ] 모델 카드(Model Card) 작성
- [ ] 라이선스 검증 (오픈소스/상용)

## 한국형 KPI 벤치마크 (공공 AI 사업)

| 지표 | 일반 수준 | 우수 수준 | 참고 출처 |
|------|---------|---------|----------|
| 분류 정확도 (Top-1) | 85% | 95%+ | KISTI 공공 AI 평가 |
| 객체 검출 mAP@0.5 | 0.7 | 0.9+ | 한국형 AI 평가 |
| 번역 BLEU | 30 | 45+ | NIA AI Hub 기준 |
| LLM 한국어 KMMLU | 50점 | 70+ | KMMLU Leaderboard |
| 추론 응답 P95 | 2초 | <500ms | 공공 챗봇 SLA |
| 학습 데이터 라벨링 정확도 | 95% | 99%+ | AI Hub 기준 |
| 모델 신뢰도 (TTA 기준) | Lv.3 | Lv.4+ | TTAK.KO-10.1407 |

## 필수 인증·표준
- **AI 신뢰성 평가** (TTA TTAK.KO-10.1407)
- **ISMS-P** + **CSAP** (개인정보 처리 시 필수)
- **AI 윤리 원칙 적합성** (과기정통부 AI 윤리기준)
- **국산 SW 가산점** (GS인증 + AI Hub 데이터 활용)
- **NIA AI 데이터 표준 적합성**

## 유사 사업 레퍼런스 (인용 가능)
- 한국어 거대언어모델 (KT MIDM, 네이버 HyperCLOVA X, LG EXAONE)
- AI Hub 학습용 데이터 (NIA) — 1,000+ 데이터셋 구축
- 정부24 AI 챗봇 (행안부)
- 119 신고접수 AI (소방청)
- 국세청 홈택스 AI 상담
- 보건복지부 AI 의료영상 분석
- 경찰청 지능형 CCTV 통합

## Win Theme 후보
1. **"검증된 한국어 AI"** — KMMLU 등 한국어 벤치마크 입증
2. **"신뢰할 수 있는 AI"** — TTA 신뢰성 Lv.4 + XAI + 편향 검증
3. **"운영 가능한 MLOps"** — 자동 재학습 + 모니터링 + 거버넌스

## Phase 4(ACTION PLAN) 필수 산출물
- AI 모델 설계서 (아키텍처, 하이퍼파라미터)
- 학습 데이터 명세 (수집·라벨링·검증 절차)
- 모델 평가 보고서 (벤치마크, 베이스라인 대비)
- MLOps 파이프라인 설계
- 모델 카드 + 데이터 카드
- AI 윤리·편향 점검 보고서
- 추론 API 설계서
- 운영·재학습 매뉴얼

## Phase 6(WHY US) 강조 포인트
- AI/ML 박사·석사 인력 수
- 정보처리기사 + 빅데이터분석기사 + ADP 보유
- 자체 학습 인프라 (GPU 클러스터 규모)
- 한국어 NLP / 한국형 CV 실적
- TTA AI 신뢰성 인증 보유 모델 수
- 국제 학회 논문 (NeurIPS, ICML, ACL, CVPR 등)
- AI Hub 데이터 구축 참여 이력
