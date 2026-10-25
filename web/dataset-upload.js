/* File selection only. The server independently validates imported samples. */
(function (root) {
  'use strict';
  const MAX_CSV_BYTES = 8_000_000;
  const MAX_HEA_BYTES = 8192;
  const MAX_DAT_BYTES = 1_600_000;
  function invalid(error) { return {kind:'invalid',error}; }
  function classify(fileList) {
    const files = Array.from(fileList || []);
    if (!files.length) return invalid('No files selected. Choose one CSV or a matched .hea and .dat pair.');
    if (files.length === 1 && /\.csv$/i.test(files[0].name)) {
      const file=files[0];
      if (!file.size || file.size>MAX_CSV_BYTES) return invalid('CSV must be nonempty and no larger than 8 MB.');
      return {kind:'csv',file};
    }
    if (files.length!==2) return invalid('Select exactly one CSV, or both a matching .hea and .dat together (hold Ctrl when selecting).');
    const header=files.find(f=>/\.hea$/i.test(f.name));
    const data=files.find(f=>/\.dat$/i.test(f.name));
    if (!header || !data) return invalid('A WFDB recording requires one .hea header and one .dat data file.');
    if (header.name.slice(0,-4).toLowerCase()!==data.name.slice(0,-4).toLowerCase())
      return invalid('Header and data filenames must match before their .hea/.dat extensions.');
    if (!header.size || !data.size || header.size>MAX_HEA_BYTES || data.size>MAX_DAT_BYTES)
      return invalid('WFDB pair must be nonempty: header <= 8,192 bytes and data <= 1,600,000 bytes.');
    return {kind:'wfdb',header,data};
  }
  root.WaveAssureDatasetUpload=Object.freeze({classify});
})(typeof window === 'undefined' ? globalThis : window);
