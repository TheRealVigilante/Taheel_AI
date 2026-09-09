# RiyadhPay (راية باي) — Customer Operations & Incident Response Manual
## دليل إجراءات العمل القياسية لخدمة العملاء والعمليات التشغيلية (SOP Manual)
**Document Version:** 3.2 | **Classification:** Internal / Confidential  
**Regulatory Alignment:** Saudi Central Bank (SAMA) Financial Consumer Protection Principles & AML/CFT Regulations  
**Primary Entity:** RiyadhPay for Digital Payments LLC (شركة راية باي للمدفوعات الرقمية)  

---

## 1. Overview & Operational Scope | نظرة عامة ونطاق العمليات

### 1.1 Purpose / الهدف
This manual establishes the mandatory Standard Operating Procedures (SOPs) for the Customer Operations (Tier-1 and Tier-2 Support) department at RiyadhPay. Every frontline specialist is required to master these procedures during their 90-day onboarding and probation period (under Saudi Labor Law Article 53).

يهدف هذا الدليل إلى توثيق وتوحيد جميع إجراءات العمل القياسية لفريق خدمة العملاء والعمليات التشغيلية (المستوى الأول والثاني) في شركة راية باي للمدفوعات الرقمية. يُلزم جميع الموظفين الجدد بإتقان هذه المعايير التشغيلية خلال فترة التجربة النظامية (المادة 53 من نظام العمل السعودي).

### 1.2 Core Systems & Tooling Stack / الأنظمة والأدوات التشغيلية
All specialists must have active two-factor authentication (2FA) credentials for the following internal and national platforms:
1. **RP-Admin Portal:** Core wallet administration, ledger balances, fee overrides, and user state toggles.
2. **Nafath National Platform (النفاذ الوطني الموحد):** National digital identity verification.
3. **SARIE Gateway (نظام سريع للمدفوعات الفورية):** Instant Interbank transfer status and reversal lookups.
4. **Zendesk Enterprise CRM:** Ticket triage, omni-channel queue management, and SLA tracking.
5. **SAMA Care Portal:** Direct escalation tracking for regulatory inquiries and consumer protection tickets.
6. **Mada / Scheme Switch Monitor:** Visa, Mastercard, and Mada settlement trace IDs.

---

## 2. Standard Operating Procedures (SOPs) | إجراءات العمل القياسية

```
SOP Catalog:
├── SOP-OPS-001: Customer Registration & Nafath Identity Verification
├── SOP-OPS-002: SARIE Instant Payment Exceptions & Stuck Transfers
├── SOP-OPS-003: Emergency Wallet Lockout & Compromised Card Response
├── SOP-OPS-004: SAMA Consumer Complaint Resolution & Escalation
├── SOP-OPS-005: AML / Fraud Red Flag Triage & Escalation
├── SOP-OPS-006: SME Merchant POS Terminal Reconciliation Inquiries
└── SOP-OPS-007: Mada / Visa Transaction Chargebacks & Dispute Handling
```

---

### SOP-OPS-001: Customer Registration & Nafath Identity Verification
**الرمز:** SOP-OPS-001 | **العنوان:** إجراءات التسجيل والتحقق من الهوية عبر نفاذ  
**Role Relevance:** Critical for Tier-1 Specialists handling account creation roadblocks, biometric mismatch, and SAMA KYC compliance.  
**Complexity:** Medium | **Target Tools:** `RP-Admin`, `Nafath Platform`, `Zendesk`  
**SLA:** 15 minutes response time for verification issues.

#### Procedure Steps / خطوات العمل:
1. **Lookup Account:** Search user by National ID / Iqama number (`NID`) in the `RP-Admin` portal under `Users > KYC Management`.
2. **Check Nafath Request Status:**
   - *Status: `PENDING_ACCEPT`* $\rightarrow$ Advise the user to open the Nafath App within 180 seconds and approve the two-digit random prompt.
   - *Status: `BIOMETRIC_EXPIRED`* $\rightarrow$ The user's Absher biometric or digital residency has expired. Direct the user to renew through Absher before retrying.
   - *Status: `SIM_OWNERSHIP_MISMATCH`* $\rightarrow$ The mobile number used in the registration does not match the CITC registered owner of the National ID.
3. **SIM Verification Fallback:** If the user changed their SIM card recently, guide them to submit proof of SIM ownership via the RiyadhPay app settings.
4. **Logging & Ticket Closure:** Categorize ticket as `KYC > Nafath Verification > [Subcategory]` and mark as resolved once the KYC badge updates to `LEVEL_2_VERIFIED`.

> ⚠️ **Common Mistake to Avoid / خطأ شائع يجب تجنبه:**  
> Never manually override a KYC block or approve an account without an authenticated Nafath callback token. Doing so is a direct violation of SAMA circular No. 41045237 and leads to immediate disciplinary review.
> يمنع منعاً باتاً التجاوز اليدوي لحالة التحقق من الهوية أو تفعيل أي حساب دون الحصول على رمز استجابة معتمد من نفاذ.

---

### SOP-OPS-002: SARIE Instant Payment Exceptions & Stuck Transfers
**الرمز:** SOP-OPS-002 | **العنوان:** معالجة تعثر الحوالات الفورية عبر نظام سريع  
**Role Relevance:** Core daily task for operations specialists addressing customer wallet debit without beneficiary credit.  
**Complexity:** High | **Target Tools:** `SARIE Gateway Console`, `RP-Admin Ledger`, `Zendesk`  
**SLA:** 30 minutes preliminary status; 2 business hours for automated reconciliation.

#### Procedure Steps / خطوات العمل:
1. **Retrieve Transaction Reference:** Request the 16-character End-to-End (`E2E`) reference code from the customer or locate the debit entry in `RP-Admin > Wallet > Transactions`.
2. **Query SARIE Gateway:**
   - Input the `E2E` code into the SARIE Monitor tool.
   - Examine the ISO 20022 response code:
     - `ACTC` (Accepted Technical Validation) $\rightarrow$ Funds cleared our system, awaiting beneficiary bank acknowledgement.
     - `RJCT` (Rejected) $\rightarrow$ Immediate refund triggered. Verify refund credit in the user's ledger within 5 minutes.
     - `ACSP` (Accepted Settlement In Process) $\rightarrow$ Transaction in progress; ask customer to wait 20 minutes before initiating a recall.
3. **Initiate Formal Recall (R-Message):** If the transaction is stuck in `ACSP` for over 2 hours during a banking system maintenance window, trigger a `camt.056` Payment Cancellation Request.
4. **Customer Communication:** Send bilingual macro response template `SARIE_PENDING_EXPLANATION` reassuring the customer that funds are guaranteed under SAMA settlement rules.

> ⚠️ **Common Mistake to Avoid / خطأ شائع يجب تجنبه:**  
> Do not ask the customer to contact the receiving bank before verifying whether RiyadhPay has received the final settlement acknowledgement (`pacs.002`). Always verify the exact ISO response code first.
> تجنب توجيه العميل للتواصل مع البنك المستلم قبل التحقق من كود الاستجابة الفعلي في بوابة سريع والتأكد من إرسال رسالة التسوية.

---

### SOP-OPS-003: Emergency Wallet Lockout & Compromised Card Response
**الرمز:** SOP-OPS-003 | **العنوان:** تجميد المحفظة والبطاقات في حالات الطوارئ والاحتيال  
**Role Relevance:** High-priority safety protocol for immediate customer protection against phishing, device theft, or unauthorized access.  
**Complexity:** Critical | **Target Tools:** `RP-Admin Security Console`, `SMS Gateway`, `Zendesk VIP Queue`  
**SLA:** Immediate (< 2 minutes execution upon verified call/chat).

#### Procedure Steps / خطوات العمل:
1. **Identity Safeguard Questions:** Before executing any manual freeze, verify:
   - National ID / Iqama number.
   - Last 4 digits of the active digital card.
   - Date and approximate amount of the last legitimate transaction.
2. **Instant Wallet Freeze:**
   - In `RP-Admin > Users > [UserID] > Security`, click **`EMERGENCY_FREEZE_ALL`**.
   - This action instantly terminates active JWT sessions, disables tokenized cards in Apple Pay / Google Wallet, and freezes outward transfers.
3. **Card Invalidation:** Mark the virtual/physical card status as `LOST_STOLEN_PERMANENT` to prevent offline auth attempts.
4. **Issue Incident Notification:** Automatically dispatch an encrypted SMS and push notification to the registered phone number detailing the temporary lockdown.
5. **Transfer to Fraud Investigation Team:** Assign the ticket with tag `#URGENT_FRAUD_LOCKOUT` to the Level-2 Risk & AML department.

> ⚠️ **Common Mistake to Avoid / خطأ شائع يجب تجنبه:**  
> Never disclose transaction amounts or recent merchant names to an inbound caller before they have successfully answered all security questions.
> لا تفصح أبداً عن تفاصيل أو مبالغ العمليات للمتصل قبل إتمام التحقق الأمني الكامل لمنع محاولات الهندسة الاجتماعية.

---

### SOP-OPS-004: SAMA Consumer Complaint Resolution & Escalation
**الرمز:** SOP-OPS-004 | **العنوان:** إدارة شكاوى البنك المركزي السعودي وحماية العملاء  
**Role Relevance:** Legal compliance workflow required for all team members to protect RiyadhPay against statutory fines.  
**Complexity:** High | **Target Tools:** `SAMA Care Portal`, `RP-Admin Legal Archive`, `Internal SLA Tracker`  
**SLA:** 5 calendar days maximum resolution; 24 hours initial response to SAMA.

#### Procedure Steps / خطوات العمل:
1. **Intake & Docketing:** Review the incoming SAMA Care ticket docket number. Cross-reference with existing Zendesk tickets.
2. **Timeline Analysis:** SAMA regulations mandate a complete resolution within **5 business days**. Check if the customer submitted an internal complaint prior to elevating to SAMA.
3. **Evidence Dossier Compilation:**
   - Pull server transaction logs with microsecond timestamps.
   - Download customer chat transcripts and voice recording references.
   - Attach relevant Terms of Service clauses accepted by the user during signup.
4. **Drafting Official SAMA Response:**
   - Responses must be submitted in formal Arabic adhering to the SAMA Financial Consumer Protection Principles format.
   - State clearly: Case Background, Findings, Root Cause, Remedial Action Taken, and Customer Communication proof.
5. **Supervisor Sign-off:** All SAMA responses must be approved by the Team Lead before submission to the SAMA Care portal.

> ⚠️ **Common Mistake to Avoid / خطأ شائع يجب تجنبه:**  
> Closing a SAMA complaint in the internal CRM before the SAMA portal reflects `CASE_CLOSED_SATISFACTORY`. Regulatory fines occur if a ticket is marked resolved internally while remaining open with the Central Bank.
> إغلاق الشكوى في النظام الداخلي قبل اعتماد إغلاقها رسمياً في بوابة "ساما كير" يعرض المنشأة لغرامات عدم الامتثال.

---

### SOP-OPS-005: AML / Fraud Red Flag Triage & Escalation
**الرمز:** SOP-OPS-005 | **العنوان:** رصد مؤشرات غسل الأموال وتصعيد العمليات المشبوهة  
**Role Relevance:** Anti-Money Laundering (AML) and Counter-Terrorism Financing (CFT) regulatory requirement under Saudi Anti-Money Laundering Law.  
**Complexity:** Critical | **Target Tools:** `AML Rule Engine`, `RP-Admin Compliance`, `Zendesk Confidential Tagging`  
**SLA:** 1 hour escalation to the Compliance & MLRO (Money Laundering Reporting Officer).

#### Procedure Steps / خطوات العمل:
1. **Identify Red Flag Triggers:**
   - Rapid velocity: Customer deposits funds via mada card and immediately initiates multiple outward SARIE transfers to third parties within 10 minutes.
   - Round-trip patterns: Inward transfers from multiple unverified accounts consolidated into one beneficiary.
   - Structural avoidance: Transactions just below the SAR 20,000 regulatory reporting threshold.
2. **Behavioral Assessment:** Check if the user's declared economic profile (e.g., student, unemployed) does not align with the monthly turnover volume.
3. **Discreet Handling (No Tipping Off):**
   - **STRICT PROHIBITION:** Never inform the customer that their account is under AML review or that a suspicious transaction report (STR) has been filed.
   - Neutral customer response: *"Your transaction is currently undergoing standard security reconciliation. We appreciate your patience."*
4. **File Internal Suspicious Activity Report (ISAR):** Complete the confidential ISAR form and dispatch to `compliance-ops@riyadhpay.sa`.

> ⚠️ **Common Mistake to Avoid / خطأ شائع يجب تجنبه:**  
> Tipping off the customer (إفشاء السرية) is a criminal offense under Article 17 of the Saudi Anti-Money Laundering Law, carrying severe legal penalties.
> يحظر إشعار أو تنبيه العميل بوجود شبهة غسل أموال أو رفع تقرير اشتباه، ويعد ذلك جريمة نظامية موجبة للمساءلة الجزائية.

---

### SOP-OPS-006: SME Merchant POS Terminal Reconciliation Inquiries
**الرمز:** SOP-OPS-006 | **العنوان:** معالجة استفسارات تسوية نقاط البيع للتجار والمنشآت  
**Role Relevance:** Merchant Operations Specialist duty addressing retail merchant payout discrepancies and terminal settlement batches.  
**Complexity:** Medium | **Target Tools:** `POS Merchant Dashboard`, `Switch Settlement Gateway`, `Zendesk Merchant Queue`  
**SLA:** 4 hours resolution; end-of-day reconciliation confirmation.

#### Procedure Steps / خطوات العمل:
1. **Identify Merchant & Terminal ID (TID):** Request the 8-digit `TID` printed on the POS terminal receipt and merchant commercial registration (`CR`) number.
2. **Inspect Batch Settlement Status:**
   - Navigate to `POS Operations > Terminals > [TID] > Daily Batches`.
   - Check if the terminal performed end-of-day automatic batch settlement (`Batch Close` at 00:00 KSA).
   - If batch status is `OPEN_UNSETTLED`: guide the merchant to trigger a manual batch closure via terminal menu `Admin > Settlement > Close Batch`.
3. **Reconcile Merchant IBAN Payout:**
   - SAMA Next-Day Settlement (T+1): Verify that net funds after interchange fee deduction (0.8% for Mada, 2.2% for Visa/Mastercard) were credited to the merchant's corporate IBAN.
4. **Provide Digital Settlement Statement:** Export the CSV/PDF daily audit statement and email it to the merchant's authorized finance contact.

> ⚠️ **Common Mistake to Avoid / خطأ شائع يجب تجنبه:**  
> Never initiate a duplicate payout before confirming whether the merchant bank account rejected the previous SARIE batch payment due to an invalid or inactive corporate IBAN.
> لا تصدر أمر تحويل مالي إضافي للتاجر قبل مطابقة سبب رفض الحوالة البنكية السابقة والتأكد من صحة الآيبان المؤسسي المسجل.

---

### SOP-OPS-007: Mada / Visa Transaction Chargebacks & Dispute Handling
**الرمز:** SOP-OPS-007 | **العنوان:** نزاعات الاعتراض المالي وعمليات الاسترداد (مدى وفيزا)  
**Role Relevance:** Specialized resolution process for unauthorized card transactions, ATM cash dispensing failures, and merchant overcharges.  
**Complexity:** High | **Target Tools:** `Mada Dispute Portal`, `Visa Resolve Online (VROL)`, `RP-Admin Disputes`  
**SLA:** 3 business days initial claim filing; 45 calendar days maximum dispute lifecycle.

#### Procedure Steps / خطوات العمل:
1. **Qualify Dispute Eligibility:**
   - Confirm the transaction occurred within the last 120 calendar days.
   - Verify transaction state is `SETTLED` (charges cannot be disputed while in `AUTH_PENDING` status).
2. **Collect Mandatory Supporting Evidence:**
   - Signed Cardholder Dispute Form (CDF).
   - Police report (mandatory for physical card theft).
   - Communication logs between cardholder and merchant showing attempted amicable resolution.
3. **File Scheme Chargeback:**
   - For Mada domestic transactions: Submit dispute reason code `Reason 53 (ATM Short Dispense)` or `Reason 71 (Unauthorized Transaction)` in the Mada Dispute system.
   - For International Visa cards: File dispute in VROL under `10.4 (Other Fraud - Card-Absent)`.
4. **Issue Provisional Credit (Conditional):** If the customer has been with RiyadhPay for over 6 months with zero prior fraud flags, credit provisional funds pending final scheme arbitration.

> ⚠️ **Common Mistake to Avoid / خطأ شائع يجب تجنبه:**  
> Filing a dispute without checking whether the merchant has already issued an automated partial refund. Duplicate claims lead to scheme arbitration penalty fees ($500 per incident).
> رفع مطالبة اعتراض مالي دون التأكد من عدم وجود عملية استرداد آلي سابقة من التاجر، مما يترتب عليه فرض غرامات تحكيم دولية على المنشأة.

---

## 3. Shift Handover & Escalation Matrix | مصفوفة التصعيد والتسليم اليومي

| Priority Level | Scenario | First Responder | Escalation Contact | Target SLA |
| :--- | :--- | :--- | :--- | :--- |
| **P1 - Critical** | Core Payment Gateway Outage / Multiple Stuck SARIE Batches | Operations Specialist | Head of Payment Infrastructure | < 15 minutes |
| **P2 - High** | VIP Corporate Client Lockout / Potential Phishing Attack | Tier-1 Agent | Fraud Risk Team Lead | < 30 minutes |
| **P3 - Medium** | SAMA Care Regulatory Inquiry / Merchant Settlement Dispute | Operations Specialist | Compliance Specialist | < 4 hours |
| **P4 - Low** | General KYC Assistance / User App Navigation Help | Tier-1 Agent | Assigned Onboarding Mentor | < 24 hours |

---

## 4. Operational Sign-off & Probation Alignment
## إقرار التدريب والالتزام بسياسات فترة التجربة

Every new employee in Customer Operations must review and demonstrate practical mastery of all 7 SOPs above during their first 90 days. Managers will conduct formal assessments at:
- **Day 14:** System Access & Basic KYC (SOP-001, SOP-003)
- **Day 30:** Instant Payments & SARIE Settlement (SOP-002, SOP-006)
- **Day 60:** Disputes, Chargebacks, and SAMA Inquiries (SOP-004, SOP-007)
- **Day 90:** Full Autonomy, AML Governance & Final Probation Verdict (SOP-005, Shift Leadership)
