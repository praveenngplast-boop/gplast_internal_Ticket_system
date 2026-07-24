document.addEventListener('DOMContentLoaded', function() {
    // 1. Character Counters
    const subjectInput = document.getElementById('id_subject');
    const subjectCounter = document.getElementById('subject_counter');
    if (subjectInput && subjectCounter) {
        subjectInput.maxLength = 150;
        subjectInput.addEventListener('input', function() {
            const count = subjectInput.value.length;
            subjectCounter.textContent = `${count} / 150`;
        });
    }

    const descInput = document.getElementById('id_description');
    const descCounter = document.getElementById('desc_counter');
    if (descInput && descCounter) {
        descInput.addEventListener('input', function() {
            const count = descInput.value.length;
            if (count < 10) {
                descCounter.textContent = `${count} characters (minimum 10)`;
                descCounter.classList.add('text-danger');
                descCounter.classList.remove('text-success');
            } else {
                descCounter.textContent = `${count} characters (minimum 10 met)`;
                descCounter.classList.remove('text-danger');
                descCounter.classList.add('text-success');
            }
        });
    }

    const screenInput = document.getElementById('id_screen_number');
    const screenCounter = document.getElementById('screen_counter');
    if (screenInput && screenCounter) {
        screenInput.addEventListener('input', function() {
            const count = screenInput.value.length;
            screenCounter.textContent = `${count} characters`;
        });
    }

    // 2. Dynamic Departments Dropdown
    const unitSelect = document.getElementById('id_unit');
    const deptSelect = document.getElementById('id_department');
    if (unitSelect && deptSelect) {
        // Function to update departments dropdown
        const updateDepartments = function() {
            const unitId = unitSelect.value;
            // Clear existing options
            deptSelect.innerHTML = '<option value="">---------</option>';
            
            if (!unitId) return;

            // Check if we are on the reports page to load both active and inactive depts
            const showAll = deptSelect.getAttribute('data-show-all') === 'true';
            const url = `/ajax/departments/?unit_id=${unitId}&show_all=${showAll}`;

            fetch(url)
                .then(response => response.json())
                .then(data => {
                    data.departments.forEach(dept => {
                        const option = document.createElement('option');
                        option.value = dept.id;
                        option.textContent = dept.name;
                        deptSelect.appendChild(option);
                    });
                })
                .catch(err => console.error("Error fetching departments: ", err));
        };

        unitSelect.addEventListener('change', updateDepartments);
        
        // If unit is pre-selected but department is empty, load active departments
        if (unitSelect.value && deptSelect.children.length <= 1) {
            updateDepartments();
        }
    }

    // 3. Attachment File Validator (Client-side)
    const attachmentInput = document.getElementById('id_attachment');
    if (attachmentInput) {
        attachmentInput.addEventListener('change', function() {
            const file = this.files[0];
            if (!file) return;

            // Max 3MB (3 * 1024 * 1024 bytes)
            const maxSize = 3 * 1024 * 1024;
            // Allowed extensions
            const allowedExtensions = /(\.pdf|\.doc|\.docx|\.xls|\.xlsx|\.png|\.jpg|\.jpeg)$/i;

            let errorMsg = "";

            if (file.size > maxSize) {
                errorMsg = "File size exceeds 3MB. Please select a smaller file.";
            } else if (!allowedExtensions.exec(file.name)) {
                errorMsg = "Unsupported file extension. Allowed formats: pdf, doc, docx, xls, xlsx, png, jpg, jpeg.";
            }

            if (errorMsg) {
                alert(errorMsg);
                this.value = ""; // Clear selection
            }
        });
    }

    // 4. Admin Creation Fields Toggle
    // In admin creation form, Reason is hidden/visible depending on "Created By"
    const roleRadios = document.getElementsByName('created_by_role');
    const reasonContainer = document.getElementById('admin_reason_container');
    const reasonSelect = document.getElementById('id_admin_creation_reason');

    if (roleRadios.length > 0 && reasonContainer && reasonSelect) {
        const toggleReason = function() {
            let selectedRole = "";
            for (let i = 0; i < roleRadios.length; i++) {
                if (roleRadios[i].checked) {
                    selectedRole = roleRadios[i].value;
                    break;
                }
            }

            if (selectedRole === 'Admin') {
                reasonContainer.style.display = 'block';
                reasonSelect.required = true;
            } else {
                reasonContainer.style.display = 'none';
                reasonSelect.required = false;
                reasonSelect.value = ""; // Clear selection
            }
        };

        for (let i = 0; i < roleRadios.length; i++) {
            roleRadios[i].addEventListener('change', toggleReason);
        }

        // Run once on load to initialize correctly
        toggleReason();
    }
});
