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

    // Menu Toggle
    const menuIcon = document.getElementById('menu-icon');
    const menuBox = document.getElementById('menu-box'); // Renamed from credits-box
    const navEnhance = document.getElementById('nav-enhance');
    const navBuilder = document.getElementById('nav-builder');

    // Enhance Views
    const enhanceView = document.getElementById('enhance-view');
    const enhanceBackBtn = document.getElementById('enhance-back-btn');
    const enhanceForm = document.getElementById('enhance-form');
    const enhanceFileInput = document.getElementById('enhance-file-input');
    const enhanceDropZone = document.getElementById('enhance-drop-zone');
    const enhanceBtn = document.getElementById('enhance-btn');
    const enhanceLoading = document.getElementById('enhance-loading');
    const enhanceResults = document.getElementById('enhance-results');
    const enhanceFileName = document.getElementById('enhance-file-name');


    menuIcon.addEventListener('click', (e) => {
        e.stopPropagation();
        menuBox.classList.toggle('hidden');
    });

    // Navigate to Enhance View (Separate Page)
    navEnhance.addEventListener('click', () => {
        window.location.href = '/enhance';
    });

    // Navigate to Resume Builder (Separate Page)
    if (navBuilder) {
        navBuilder.addEventListener('click', () => {
            window.location.href = '/builder';
        });
    }

    enhanceBackBtn.addEventListener('click', () => {
        switchView('upload');
        enhanceForm.reset();
        enhanceResults.classList.add('hidden');
        enhanceResults.innerHTML = '';
        enhanceFileName.classList.add('hidden');
    });

    // Close menu when clicking outside
    document.addEventListener('click', (e) => {
        if (!menuBox.contains(e.target) && !menuIcon.contains(e.target)) {
            menuBox.classList.add('hidden');
        }
    });

    // Enhance Drag & Drop
    enhanceDropZone.addEventListener('dragover', (e) => { e.preventDefault(); enhanceDropZone.classList.add('dragover'); });
    enhanceDropZone.addEventListener('dragleave', () => { enhanceDropZone.classList.remove('dragover'); });
    enhanceDropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        enhanceDropZone.classList.remove('dragover');
        if (e.dataTransfer.files.length) {
            enhanceFileInput.files = e.dataTransfer.files;
            handleEnhanceFileSelect();
        }
    });

    enhanceFileInput.addEventListener('change', handleEnhanceFileSelect);

    function handleEnhanceFileSelect() {
        if (enhanceFileInput.files.length) {
            enhanceFileName.textContent = `Selected: ${enhanceFileInput.files[0].name}`;
            enhanceFileName.classList.remove('hidden');
            enhanceBtn.disabled = false;
        }
    }

    // Enhance Form Submit
    enhanceForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData();
        formData.append('resume', enhanceFileInput.files[0]);

        enhanceLoading.classList.remove('hidden');
        enhanceResults.classList.add('hidden');
        enhanceBtn.disabled = true;

        try {
            const response = await fetch('/enhance-cv', { method: 'POST', body: formData });
            const data = await response.json();

            if (data.suggestions) {
                enhanceResults.innerHTML = data.suggestions;
                enhanceResults.classList.remove('hidden');
            } else {
                alert(data.error || 'Error enhancing CV');
            }
        } catch (err) {
            alert('An error occurred.');
        } finally {
            enhanceLoading.classList.add('hidden');
            enhanceBtn.disabled = false;
        }
    });

    function switchView(viewName) {
        // Hide all views
        uploadView.classList.remove('active');
        uploadView.classList.add('hidden');
        dashboardView.classList.remove('active');
        dashboardView.classList.add('hidden');
        enhanceView.classList.remove('active');
        enhanceView.classList.add('hidden');

        if (viewName === 'dashboard') {
            dashboardView.classList.remove('hidden');
            setTimeout(() => dashboardView.classList.add('active'), 10);
        } else if (viewName === 'enhance') {
            enhanceView.classList.remove('hidden');
            setTimeout(() => enhanceView.classList.add('active'), 10);
        } else {
            uploadView.classList.remove('hidden');
            setTimeout(() => uploadView.classList.add('active'), 10);
        }
    }

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

        // Render Technical Skills
        const techSkillsList = document.getElementById('tech-skills-list');
        techSkillsList.innerHTML = '';
        currentSkills = [...(data.technical_skills || []), ...(data.soft_skills || [])]; // Combine for cover letter

        const techSkills = data.technical_skills || [];
        if (techSkills.length === 0 && data.skills) {
            // Fallback if old format
            currentSkills = data.skills;
            currentSkills.forEach(skill => {
                const span = document.createElement('span');
                span.classList.add('tag');
                span.textContent = skill;
                techSkillsList.appendChild(span);
            });
        } else {
            techSkills.forEach(skill => {
                const span = document.createElement('span');
                span.classList.add('tag');
                span.textContent = skill;
                techSkillsList.appendChild(span);
            });
        }

        // Render Soft Skills
        const softSkillsList = document.getElementById('soft-skills-list');
        softSkillsList.innerHTML = '';
        const softSkills = data.soft_skills || [];
        softSkills.forEach(skill => {
            const span = document.createElement('span');
            span.classList.add('tag');
            span.style.borderColor = 'var(--secondary-color)';
            span.textContent = skill;
            softSkillsList.appendChild(span);
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

            // Build Search URLs
            const linkedInUrl = `https://www.linkedin.com/jobs/search/?keywords=${encodeURIComponent(roleObj.title)}`;
            const naukriUrl = `https://www.naukri.com/jobs-in-india?k=${encodeURIComponent(roleObj.title)}`;
            const indeedUrl = `https://in.indeed.com/jobs?q=${encodeURIComponent(roleObj.title)}`;

            card.innerHTML = `
                <span class="role-title">${roleObj.title}</span>
                <p>${roleObj.description}</p>
                <div class="job-buttons">
                    <a href="${linkedInUrl}" target="_blank" class="btn-job btn-linkedin">LinkedIn ↗</a>
                    <a href="${naukriUrl}" target="_blank" class="btn-job btn-naukri">Naukri ↗</a>
                    <a href="${indeedUrl}" target="_blank" class="btn-job btn-indeed">Indeed ↗</a>
                </div>
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
