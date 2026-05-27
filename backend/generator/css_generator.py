def get_modal_css():

    return """
<style>

.t-Body-contentInner {
    padding: 0 !important;
}

.t-Region {
    border: none !important;
    box-shadow: none !important;
    background: transparent !important;
}

.t-Region-body {
    padding: 0 !important;
}

.react-modal-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,0.45);
    backdrop-filter: blur(4px);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 9999;
}

.react-modal-card {
    width: 768px;
    max-width: calc(100vw - 40px);
    background: #ffffff;
    border-radius: 22px;
    overflow: hidden;
    box-shadow: 0 24px 60px rgba(0,0,0,0.25);
    font-family: Arial, sans-serif;
}

.react-modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 28px 36px;
    border-bottom: 1px solid #e5e7eb;
}

.react-modal-title {
    font-size: 24px;
    font-weight: 600;
    color: #111827;
}

.react-modal-close {
    font-size: 30px;
    color: #94a3b8;
}

.react-modal-body {
    padding: 32px 36px 24px;
}

.t-Form-fieldContainer {
    margin-bottom: 22px !important;
}

.t-Form-label {
    font-size: 16px !important;
    font-weight: 600 !important;
    color: #334155 !important;
    margin-bottom: 8px !important;
}

.t-Form-inputContainer {
    width: 100% !important;
}

.react-input,
.apex-item-text,
.apex-item-select,
input[type="text"],
input[type="number"],
select,
textarea {
    width: 100% !important;
    height: 62px !important;
    border: 1px solid #dbe2ea !important;
    border-radius: 12px !important;
    padding: 0 18px !important;
    font-size: 20px !important;
    outline: none !important;
    box-shadow: none !important;
    background: #ffffff !important;
}

.react-input:focus,
input[type="text"]:focus,
input[type="number"]:focus,
select:focus,
textarea:focus {
    border-color: #0284c7 !important;
}

.react-modal-footer {
    display: flex;
    gap: 18px;
    padding: 8px 36px 32px;
}

.react-btn {
    flex: 1;
    height: 60px;
    border: none;
    border-radius: 12px;
    font-size: 20px;
    font-weight: 600;
    cursor: pointer;
}

.react-btn-primary {
    background: #0284c7;
    color: white;
}

.react-btn-secondary {
    background: #eef2f7;
    color: #334155;
}

</style>
"""