# 도메인 카드 — 인프라 / 클라우드 / 시스템

> 공공입찰(나라장터) 대상 인프라/클라우드/시스템 구축 사업 제안서.

## 사업 유형 시그널 (RFP 키워드)
"인프라 구축", "서버 도입", "스토리지", "네트워크 구축", "데이터센터(IDC)",
"클라우드 전환", "K-Cloud", "퍼블릭/프라이빗/하이브리드 클라우드",
"가상화", "컨테이너", "쿠버네티스", "마이크로서비스", "DevOps",
"백업/DR", "재해복구", "이중화", "HA", "망분리", "시스템 통합(SI)",
"통합 운영 관리", "ITSM", "모니터링", "보안 인프라"

## 정책·법제 연계
- **공공기관 정보자원 통합 가이드** (행안부)
- **클라우드 컴퓨팅법** (2015) — 공공기관 클라우드 활용 의무
- **K-Cloud (디지털플랫폼정부)** — 국산 클라우드 우선 도입
- **CSAP (클라우드 보안 인증)** — 공공 클라우드 필수
- **국가정보통신망 보안업무 규정** — 망분리 의무
- **공공기관 정보자원 통합·관리지침** — IDC 통합·이전
- **데이터센터법** (2022) — 재난·안전 의무

## 표준 아키텍처
```
[L7]   웹/앱 (Tomcat/Nginx, K8s, Service Mesh)
[L4]   로드밸런서 (LB, F5/A10)
[보안] WAF / IPS / IDS / Anti-DDoS / NAC
[가상] VMware / KVM / Hyper-V / OpenStack
[K8s]  쿠버네티스 / Rancher / OpenShift
[저장] SAN / NAS / 분산스토리지(Ceph)
[백업] Commvault / Veeam / NetBackup
[감시] Zabbix / Prometheus / Grafana / ELK / Splunk
```

핵심 스택:
- **클라우드(국산)**: NHN Cloud, KT Cloud, Naver Cloud, Samsung SDS, NIPA G-Cloud
- **클라우드(글로벌)**: AWS, Azure, GCP — 공공 부문은 CSAP 인증 리전만 가능
- **가상화**: VMware vSphere, KVM, Proxmox, Citrix
- **컨테이너**: Kubernetes, Docker, Helm, Argo CD, Istio
- **자동화**: Ansible, Terraform, Jenkins, GitLab CI
- **모니터링**: Zabbix, Prometheus, Grafana, ELK, Datadog
- **보안**: 시큐어OS, EDR, SIEM, NAC, DRM, DLP

## 기술 요구사항 체크리스트
- [ ] 망분리 (물리/논리) — 공공기관 의무
- [ ] 이중화·고가용성 (HA) — Active-Active 또는 Active-Standby
- [ ] 재해복구(DR) — RTO/RPO 명시
- [ ] 백업 (3-2-1 원칙: 3 copies, 2 media, 1 offsite)
- [ ] 보안 통제 (방화벽·WAF·IPS·EDR·DRM)
- [ ] 정보보안 정책 적합성
- [ ] 성능 SLA (응답시간·처리량·동시접속)
- [ ] 확장성 (수평/수직, Auto-Scaling)
- [ ] 접근통제 (계정·권한·MFA·감사로그)

## 한국형 KPI 벤치마크 (공공 인프라 사업)

| 지표 | 일반 수준 | 우수 수준 | 참고 출처 |
|------|---------|---------|----------|
| 시스템 가용성 | 99.5% | 99.99% (4-nine) | 정부 IDC 표준 |
| 응답시간 (P95) | 3초 | <1초 | 정부24 SLA |
| 동시접속자 | 1만 | 10만+ | 대국민 시스템 |
| RTO (복구목표시간) | 24시간 | <4시간 | 공공 DR 표준 |
| RPO (복구목표시점) | 24시간 | <1시간 | 공공 DR 표준 |
| 처리량 (TPS) | 1,000 | 10,000+ | 행정 시스템 |
| 보안 침해 대응 | 24h | <1h | KISA 가이드 |

## 필수 인증·표준
- **CSAP** (Cloud Security Assurance Program) — IaaS/SaaS/PaaS 인증
- **ISMS-P** (정보보호 및 개인정보보호 관리체계)
- **ISO/IEC 27001** — 정보보안 국제표준
- **SOC 1/2/3** — 클라우드 운영 인증
- **GS인증** — 국산 SW 활용 시 가산점
- **CC인증 (Common Criteria)** — 보안제품 EAL 등급
- **TTA 인증** — 정보통신 표준 적합

## 유사 사업 레퍼런스
- 정부통합전산센터 (NIRS) — 1·2·3센터
- 디지털플랫폼정부 G-클라우드
- 우정사업본부 데이터센터
- 한전 EMS 차세대 시스템
- 국세청 차세대 홈택스
- 건강보험심사평가원 차세대 시스템
- 국방부 국방통합정보관리소
- 서울시 클라우드 데이터센터

## Win Theme 후보
1. **"검증된 안정성"** — 99.9% 가용성 + 다년 무중단 운영 실적
2. **"국산 우선·보안 강화"** — K-Cloud + CSAP + 국산 보안제품 통합
3. **"단계적 클라우드 전환"** — 리스크 최소화 마이그레이션 방법론

## Phase 4(ACTION PLAN) 필수 산출물
- 시스템 구성도 (Logical/Physical/Network)
- 용량 산정서 (서버/스토리지/네트워크)
- 구축 일정표 (WBS 200+ 항목)
- 마이그레이션 계획서 (단계별 전환)
- 보안 설계서 (망구성·접근통제·암호화)
- 백업·DR 계획서
- 성능 시험 계획서
- 운영 인수인계서

## Phase 5(MANAGEMENT) 필수 항목
- 정보보호 관리 체계 (CISO 보고)
- 형상관리 (CMDB 기반)
- 변경관리 (CAB 운영)
- 사고관리 (CSIRT)
- ITIL 기반 ITSM
- 망분리 운영 절차

## Phase 6(WHY US) 강조 포인트
- 정보처리기술사·정보관리기술사·정보통신기술사 보유
- 정보처리기사·CISA·CISSP·AWS/Azure 자격
- ISMS-P 인증 보유
- 공공 IDC 운영 실적 (연수 / 시스템 수)
- 클라우드 전환 사업 수행 실적
- 24/7 NOC 운영 인력 규모
- 무중단 가동시간 누적 기록
