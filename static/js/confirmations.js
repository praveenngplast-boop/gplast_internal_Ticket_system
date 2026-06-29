document.addEventListener('DOMContentLoaded', function() {
    let currentFormToSubmit = null;
    let currentModal = null;
    
    // Grab/create confirmation modal elements
    const modalEl = document.getElementById('confirmModal');
    if (!modalEl) return;
    
    const confirmModalBody = document.getElementById('confirmModalBody');
    const confirmModalYesBtn = document.getElementById('confirmModalYesBtn');
    
    // Initialize bootstrap modal
    const bsConfirmModal = new bootstrap.Modal(modalEl);

    // Intercept Form Submissions
    document.addEventListener('submit', function(e) {
        const form = e.target;
        
        // If it's already verified and confirmed, let it submit
        if (form.classList.contains('confirmed')) {
            return;
        }

        let confirmMsg = "";

        // 1. Dynamic check for special forms
        
        // Ticket Assign Form
        if (form.id === 'assignForm') {
            const nameInput = form.querySelector('[name="assigned_person"]');
            if (nameInput) {
                const name = nameInput.value.trim();
                if (!name) return; // Let normal validation handle empty
                confirmMsg = `Assign this ticket to ${name}?`;
            }
        }
        
        // Ticket Close Form
        else if (form.id === 'closeForm') {
            confirmMsg = "Are you sure you want to close this ticket?";
        }
        
        // Ticket Hold Form
        else if (form.id === 'holdForm') {
            confirmMsg = "Move this ticket to Hold?";
        }
        
        // Ticket Escalate Form
        else if (form.id === 'escalateForm') {
            confirmMsg = "Are you sure you want to escalate this ticket to the ERP vendor?";
        }

        // Generic forms with data-confirm attribute
        else if (form.hasAttribute('data-confirm')) {
            confirmMsg = form.getAttribute('data-confirm');
        }

        // Trigger confirmation modal if message exists
        if (confirmMsg) {
            e.preventDefault();
            currentFormToSubmit = form;
            confirmModalBody.textContent = confirmMsg;
            bsConfirmModal.show();
        }
    });

    // Handle Yes Button Click
    confirmModalYesBtn.addEventListener('click', function() {
        if (currentFormToSubmit) {
            currentFormToSubmit.classList.add('confirmed');
            
            // If it's a link click trigger instead of form submit
            if (currentFormToSubmit.tagName === 'A') {
                window.location.href = currentFormToSubmit.href;
            } else {
                currentFormToSubmit.submit();
            }
            
            bsConfirmModal.hide();
            currentFormToSubmit = null;
        }
    });

    // Handle inline anchor actions (e.g. Export Reports, Deactivating units directly via link)
    // We can add class="confirm-link" and data-confirm="Message..."
    document.addEventListener('click', function(e) {
        const anchor = e.target.closest('.confirm-link');
        if (anchor) {
            // Check if already confirmed
            if (anchor.classList.contains('confirmed')) {
                return;
            }
            e.preventDefault();
            currentFormToSubmit = anchor;
            confirmModalBody.textContent = anchor.getAttribute('data-confirm') || "Are you sure you want to perform this action?";
            bsConfirmModal.show();
        }
    });
});
