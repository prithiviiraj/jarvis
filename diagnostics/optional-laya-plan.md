# Optional real Laya validation

Not yet executed. Separate CPU diagnostic, no owner data or browser effects.

- Laya0.3.27wheel is322,956bytes but depends on Torch/Transformers. The reviewed English checkpoint is842,609,210bytes, multilingual643,835,514bytes. It is not a tiny16MBcomponent.
- Pin English checkpoint revision7b928d828b7b0e022f929d9bd2e44165aa270148 andSHA256891102d372688fc2a094dac56a384bc537b87c63f21f9f3dac0be2b7cbc8d86c.
- Install CPU Torch2.6.0 from official PyTorch CPU index, then the pinned diagnostic requirements. Dependency compatibility still needs real installation.
- Run actualcheckpoint with synthetic boundedquestions, normalizeactualwiremetadata, requireabstentionorreview-onlyproposal. No model answer is a user approval or a browser completion.
- Report cold+warmCPUsynthesis-equivalentdecisiontime andpeakRAM; do notreuseupstream33msT4claimaslaptopbenchmark.
- Release checkpoint afteracceptance, neverbundleweightsindefaultportable. ShippinganoptionalengineEXEneedsanothernativepackaging/loopbackcheck.

Sources: https://pypi.org/pypi/laya/json ; https://huggingface.co/api/models/convaiinnovations/laya?blobs=true ; https://github.com/NandhaKishorM/laya ; https://raw.githubusercontent.com/NandhaKishorM/laya/main/laya/serve.py .
