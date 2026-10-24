# WaveAssure — Indian Medical Device Software Regulatory Pathway
**Working planning document · 24 October 2026 · NOT an authorization, licence, regulatory classification, or legal opinion.**

## Two distinct intended uses: do not mix them

**Current research version:** Local retrospective waveform analysis, signal integrity experiments, offline research reviews on licensed/de-identified data. No diagnosis, bedside alarm prioritization, medical actions, cloud or hospital networking. Source code is not hospital grade.

**Potential future regulated product (PROPOSED; NOT APPROVED):** Standalone software intended for appropriately trained clinical users to classify VT alarm events from validated monitoring inputs. This can influence decisions concerning a critical condition. Regulatory classification must be confirmed by CDSCO under MDR 2017 and the July 2026 MDSW guidance; do NOT automatically assume Class A/B/C/D. Any real-time monitoring, alarm routing or suppression would significantly change the intended use and hazards.

## Official Indian roadmap
1. **Legal manufacturer and clinical sponsor:** Identify responsible legal entity, medical/clinical lead, QA/RA contact, and quality owner. A student's repository is not a functioning manufacturer QMS.
2. **Freeze intended use and claims:** Specify population, care setting, patient monitor compatibility, input channels, outputs, user, clinical workflow, failure response, and boundaries (no automatic alarm suppression). Do not develop clinical claims first and justify them afterward.
3. **Risk classification:** Search CDSCO published classification lists. If not covered, request classification via [CDSCO MD Online](https://cdscomdonline.gov.in/). The 2026 guidance says intended use controls classification; see its §7.
4. **Build organizational QMS:** Implement ISO 13485-aligned processes, controlled documents, personnel training, design reviews, supplier management, CAPA, complaints, post-market surveillance and audited lifecycle processes. Seek an accredited certification body for ISO 13485 certification if appropriate. A certificate of the QMS is not a marketing licence for the software.
5. **Produce design-control evidence:** software requirements, architecture, threat model, source configuration, bill of materials, reproducible data pipeline, data provenance, change control, verification, software hazard analysis (ISO 14971), usability evaluation (IEC 62366-1), cybersecurity lifecycle (IEC 81001-5-1), health software safety (IEC 82304-1), lifecycle documentation (IEC 62304), and AI model verification. Obtain official standards; checklist documents alone do not establish conformity.
6. **Analytical and clinical evidence:** Freeze train/validation/test data and model version; use patient/site separated held-out datasets, predeclare clinically appropriate safety endpoints/thresholds, subpopulation performance, confidence intervals, calibration, failure analysis, independent labels and external-site testing. Never use test data to choose thresholds or make claims before results exist.
7. **Test/evaluation permission when applicable:** CDSCO 2026 MDSW guidance §12.1 describes MD-12 application -> MD-13 test licence for small-quantity manufacture/deployment for test, evaluation, demonstration or training; submit via [NSWS](https://www.nsws.gov.in/). A test licence is NOT permission to use the software for clinical care or substitute for all study permissions.
8. **Research site and ethics:** Obtain a collaborating hospital, qualified Principal Investigator, data sharing agreement, security review and assessment from an appropriately registered ethics committee **before starting a new hospital study**. DHR registration is relevant for biomedical and health research ECs; investigational regulated device studies have specific CDSCO EC requirements. Whether retrospective deidentified hospital data need full approval or exemption is for the competent ethics committee and site to decide in writing.
9. **Clinical investigation where required:** For investigational medical device software, 2026 CDSCO guidance §12.2 and MDR Chapter VII describe MD-22 application -> MD-23 permission from the Central Licensing Authority and site EC approvals. Registration on [CTRI](https://ctri.nic.in/Clinicaltrials/faq.php) before the start is required/expected for applicable trials; consult the site regulatory office on applicability to the particular study. An observer-only/silent clinical study is still not automatically exempt from regulatory or ethics review.
10. **Commercial/manufacturing authorization:** After applicable clinical evidence and regulatory review, pursue the class-specific manufacturing/import marketing licence; investigational products without predicate may need MD-26 -> MD-27 permission under §12.3. Class A/B manufacturing authorities differ from Class C/D. Do not deploy for patient-care until all required authorizations, validation and site controls are in place.
11. **Postmarket operations:** Validated cybersecurity patching, incident handling, complaint investigation, monitoring of drift, postmarket surveillance, change-control and recall capabilities as applicable.

## Critical regulator vs certificate distinctions
- CDSCO decides medical-device classification/permissions; a code audit does not.
- An accredited registrar may certify **manufacturer QMS ISO 13485**; it does not by itself clear the software as a medical device.
- IEC 62304/ISO 14971 are development/risk standards for which documented conformity can be assessed; do not refer to a simplistic "IEC 62304 product certificate" as a universal approval.
- **IEC 60601-1-8** concerns alarm systems of medical electrical equipment; applicability to a standalone research algorithm depends on the eventual system and intended integration; it is not automatically an applicable standalone product certificate.
- Hospital IEC/EC ethics clearance, permission to access hospital records, CDSCO investigation permissions and marketing licence are separate things.
- **Laboratory certification** (for a testing laboratory) is not the same as medical-device software market permission. Do not claim NABL/ISO 15189 laboratory accreditation makes an algorithm clinically approved.

## Authoritative links (checked October 2026)
- [CDSCO MDSW 2026 official guidance PDF](https://www.cdsco.gov.in/opencms/export/sites/CDSCO_WEB/Pdf-documents/Guidance-document-on-Medical-Device-Software-under-MDR-2017.pdf) (read Sections 6–12 and applicable annexures).
- [CDSCO official Medical Device portal](https://www.cdsco.gov.in/opencms/opencms/en/Medical-Device-Diagnostics/Medical-Device-Diagnostics/)
- [CDSCO Online Portal](https://cdscomdonline.gov.in/)
- [NSWS test licence portal](https://www.nsws.gov.in/)
- [DHR ethics committee registration information](https://ethics.ncdirindia.org/Registration_of_EC_reviewing.aspx)
- [CTRI official FAQ](https://www.ctri.nic.in/Clinicaltrials/faq.php)
- [NABCB accreditation directory](https://nabcb.qci.org.in/management-system-certification/)
