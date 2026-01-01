document.addEventListener('DOMContentLoaded', () => {
    const uploadForm = document.getElementById('upload-form');
    const fileInput = document.getElementById('file-input');
    const dropZone = document.getElementById('drop-zone');
    const analyzeBtn = document.getElementById('analyze-btn');
    const fileNameDisplay = document.getElementById('file-name');
    const loadingDiv = document.getElementById('loading');

    // Views
    const uploadView = document.getElementById('upload-view');
    const dashboardView = document.getElementById('dashboard-view');
    const backBtn = document.getElementById('back-btn');

    // Dashboard Elements
    const skillsList = document.getElementById('skills-list');
    const rolesList = document.getElementById('roles-list');
    const clRoleSelect = document.getElementById('cl-role-select');
    const generateClBtn = document.getElementById('generate-cl-btn');
    const clLoading = document.getElementById('cl-loading');
    const clOutput = document.getElementById('cl-output');
    const clNameInput = document.getElementById('cl-name');

    // State
    let currentSkills = [];

    // Drag & Drop
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        if (e.dataTransfer.files.length) {
            fileInput.files = e.dataTransfer.files;
            handleFileSelect();
        }
    });

    fileInput.addEventListener('change', handleFileSelect);

    function handleFileSelect() {
        if (fileInput.files.length) {
            const file = fileInput.files[0];
            fileNameDisplay.textContent = `Selected: ${file.name}`;
            fileNameDisplay.classList.remove('hidden');
            analyzeBtn.disabled = false;
        }
    }

    // Upload & Analyze
    uploadForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const formData = new FormData();
        formData.append('resume', fileInput.files[0]);

        loadingDiv.classList.remove('hidden');
        analyzeBtn.disabled = true;

        try {
            const response = await fetch('/analyze', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.error) {
                alert(data.error);
                return;
            }

            renderDashboard(data);
            switchView('dashboard');
        } catch (err) {
            console.error(err);
            alert('An error occurred during analysis.');
        } finally {
            loadingDiv.classList.add('hidden');
            analyzeBtn.disabled = false;
        }
    });

    function renderDashboard(data) {
        // Render ATS Score
        const atsScore = data.ats_score || 0;
        const atsCircle = document.getElementById('ats-circle');
        const atsText = document.getElementById('ats-text');

        // Update SVG stroke-dasharray (score, 100)
        atsCircle.setAttribute('stroke-dasharray', `${atsScore}, 100`);
        atsText.textContent = `${atsScore}%`;

        // Render ATS Tips
        const atsTipsList = document.getElementById('ats-tips-list');
        atsTipsList.innerHTML = '';
        const tips = data.ats_tips || [];
        tips.forEach(tip => {
            const li = document.createElement('li');
            li.textContent = tip;
            atsTipsList.appendChild(li);
        });

        // Render Skills
        skillsList.innerHTML = '';
        currentSkills = data.skills || [];
        currentSkills.forEach(skill => {
            const span = document.createElement('span');
            span.classList.add('tag');
            span.textContent = skill;
            skillsList.appendChild(span);
        });

        // Render Missing Skills (Gap Analysis)
        const missingSkillsList = document.getElementById('missing-skills-list');
        if (missingSkillsList) {
            missingSkillsList.innerHTML = '';
            const missing = data.missing_skills || [];
            if (missing.length === 0) {
                missingSkillsList.innerHTML = '<p class="small" style="color:#48bb78">Great job! No critical gaps found.</p>';
            }
            missing.forEach(item => {
                const div = document.createElement('div');
                div.className = 'gap-item';
                div.innerHTML = `<span class="gap-skill-name">${item.skill}</span><span class="gap-rec">Tip: ${item.recommendation}</span>`;
                missingSkillsList.appendChild(div);
            });
        }

        // Render Roles with LinkedIn Button
        rolesList.innerHTML = '';
        clRoleSelect.innerHTML = '<option value="">Select Target Role</option>';

        const roles = data.job_roles || [];
        roles.forEach(roleObj => {
            // Card
            const card = document.createElement('div');
            card.className = 'role-card';

            // Build LinkedIn Search URL
            const linkedInUrl = `https://www.linkedin.com/jobs/search/?keywords=${encodeURIComponent(roleObj.title)}`;

            card.innerHTML = `
                <span class="role-title">${roleObj.title}</span>
                <p>${roleObj.description}</p>
                <a href="${linkedInUrl}" target="_blank" class="btn-linkedin">Find on LinkedIn ↗</a>
            `;
            rolesList.appendChild(card);

            // Select Option
            const option = document.createElement('option');
            option.value = roleObj.title;
            option.textContent = roleObj.title;
            clRoleSelect.appendChild(option);
        });
    }

    function switchView(viewName) {
        if (viewName === 'dashboard') {
            uploadView.classList.remove('active');
            uploadView.classList.add('hidden');
            dashboardView.classList.remove('hidden');
            setTimeout(() => dashboardView.classList.add('active'), 50);
        } else {
            dashboardView.classList.remove('active');
            dashboardView.classList.add('hidden');
            uploadView.classList.remove('hidden');
            setTimeout(() => uploadView.classList.add('active'), 50);
        }
    }

    backBtn.addEventListener('click', () => {
        switchView('upload');
        // Reset form
        uploadForm.reset();
        fileNameDisplay.classList.add('hidden');
        analyzeBtn.disabled = true;
        clOutput.classList.add('hidden');
        clOutput.textContent = '';
    });

    // Generate Cover Letter
    generateClBtn.addEventListener('click', async () => {
        const name = clNameInput.value.trim();
        const role = clRoleSelect.value;

        if (!name || !role) {
            alert('Please enter your name and select a role.');
            return;
        }

        clLoading.classList.remove('hidden');
        clOutput.classList.add('hidden');
        generateClBtn.disabled = true;

        try {
            const response = await fetch('/generate-cover-letter', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: name,
                    role: role,
                    skills: currentSkills
                })
            });

            const data = await response.json();

            if (data.cover_letter) {
                clOutput.textContent = data.cover_letter;
                clOutput.classList.remove('hidden');
            } else {
                alert('Failed to generate cover letter.');
            }
        } catch (err) {
            console.error(err);
            alert('Error generating cover letter.');
        } finally {
            clLoading.classList.add('hidden');
            generateClBtn.disabled = false;
        }
    });
});
