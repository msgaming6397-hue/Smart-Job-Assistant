document.addEventListener('DOMContentLoaded', () => {
    const uploadForm = document.getElementById('upload-form');
    const fileInput = document.getElementById('file-input');
    const dropZone = document.getElementById('drop-zone');
    const analyzeBtn = document.getElementById('analyze-btn');
    const fileNameDisplay = document.getElementById('file-name');
    const loadingDiv = document.getElementById('loading');

    // Theme Toggle
    const toggleSwitch = document.querySelector('.theme-switch input[type="checkbox"]');
    const currentTheme = localStorage.getItem('theme');

    if (currentTheme) {
        document.body.classList.add(currentTheme);
        if (currentTheme === 'light-mode') {
            toggleSwitch.checked = true;
        }
    }

    toggleSwitch.addEventListener('change', function (e) {
        if (e.target.checked) {
            document.body.classList.add('light-mode');
            localStorage.setItem('theme', 'light-mode');
        } else {
            document.body.classList.remove('light-mode');
            localStorage.setItem('theme', 'dark-mode');
        }
    });

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

    // Navigate to Enhance View (Internal SPA with Background Change)
    navEnhance.addEventListener('click', () => {
        // Switch to enhance view
        uploadView.classList.add('hidden');
        dashboardView.classList.add('hidden');
        enhanceView.classList.remove('hidden');
        enhanceView.classList.add('active');
        menuBox.classList.add('hidden'); // Close menu

        // Change Background to Data Stream
        document.body.className = 'bg-data-stream';
        const layer = document.getElementById('bg-layer');
        if (layer) {
            layer.innerHTML = '';
            for (let i = 0; i < 20; i++) {
                const col = document.createElement('div');
                col.className = 'stream-col';
                col.style.left = Math.random() * 100 + '%';
                col.style.animationDuration = (2 + Math.random() * 3) + 's';
                col.style.animationDelay = Math.random() * 2 + 's';
                layer.appendChild(col);
            }
        }
    });

    // Navigate to Resume Builder (Separate Page)
    if (navBuilder) {
        navBuilder.addEventListener('click', () => {
            window.location.href = '/builder';
        });
    }

    const navInterview = document.getElementById('nav-interview');
    if (navInterview) {
        navInterview.addEventListener('click', () => {
            window.location.href = '/interview';
        });
    }

    const navRoadmap = document.getElementById('nav-roadmap');
    if (navRoadmap) {
        navRoadmap.addEventListener('click', () => {
            window.location.href = '/roadmap';
        });
    }

    enhanceBackBtn.addEventListener('click', () => {
        // Switch back to upload view
        enhanceView.classList.add('hidden');
        uploadView.classList.remove('hidden');
        uploadView.classList.add('active');

        enhanceForm.reset();
        enhanceResults.classList.add('hidden');
        enhanceResults.innerHTML = '';
        enhanceFileName.classList.add('hidden');

        // Restore Floating Docs Background
        document.body.className = 'bg-floating-docs';
        const layer = document.getElementById('bg-layer');
        if (layer) {
            layer.innerHTML = '';
            for (let i = 0; i < 15; i++) {
                const doc = document.createElement('div');
                doc.className = 'doc-icon';
                doc.style.left = Math.random() * 100 + '%';
                doc.style.animationDuration = (10 + Math.random() * 10) + 's';
                doc.style.animationDelay = Math.random() * 5 + 's';
                layer.appendChild(doc);
            }
        }
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

    // Export Dashboard PDF
    const exportReportBtn = document.getElementById('export-report-btn');
    if (exportReportBtn) {
        exportReportBtn.addEventListener('click', () => {
            const dashboardContent = document.getElementById('dashboard-view');

            // Create a dedicated container for the PDF
            const pdfContainer = document.createElement('div');

            // Gather sections to include
            const cloneContent = (selector) => {
                const el = dashboardContent.querySelector(selector);
                if (el) return el.cloneNode(true);
                return null;
            };

            const skillsSection = cloneContent('.skills-table-container');
            const gapSection = cloneContent('.gap-wrapper');
            const rolesSection = cloneContent('.roles-wrapper');

            // --- Construct PDF Layout ---

            // Title
            const title = document.createElement('h1');
            title.textContent = "AI Career Analysis Report";
            title.style.textAlign = 'center';
            title.style.fontFamily = 'Helvetica, sans-serif';
            title.style.marginBottom = '30px';
            title.style.color = '#111';
            pdfContainer.appendChild(title);

            // ATS Score (Text Representation)
            const scoreText = document.getElementById('ats-text').textContent;
            const atsDiv = document.createElement('div');
            atsDiv.style.marginBottom = '20px';
            atsDiv.style.padding = '20px';
            atsDiv.style.border = '1px solid #ddd';
            atsDiv.style.borderRadius = '8px';
            atsDiv.innerHTML = `<h2 style="margin:0; color:#333;">ATS Score: <span style="color:#4f46e5;">${scoreText}</span></h2>`;
            pdfContainer.appendChild(atsDiv);

            // Helper to add section
            const addSection = (titleText, contentNode) => {
                if (contentNode) {
                    const section = document.createElement('div');
                    section.style.marginBottom = '25px';
                    const h3 = document.createElement('h3');
                    h3.textContent = titleText;
                    h3.style.color = '#333';
                    h3.style.borderBottom = '1px solid #eee';
                    h3.style.paddingBottom = '5px';
                    section.appendChild(h3);

                    // Style specific children for print
                    contentNode.style.display = 'block';
                    contentNode.style.color = '#000';
                    contentNode.style.width = '100% !important';
                    contentNode.style.flexWrap = 'wrap !important';

                    // Specific fix for skills pills
                    const pills = contentNode.querySelectorAll('.tag');
                    pills.forEach(p => {
                        p.style.display = 'inline-block';
                        p.style.border = '1px solid #999';
                        p.style.padding = '5px 10px';
                        p.style.borderRadius = '15px';
                        p.style.margin = '2px';
                        p.style.color = '#000';
                        p.style.background = '#f0f0f0';
                    });
                    // Specific fix for cards (roles/gaps)
                    const cards = contentNode.querySelectorAll('.role-card, .menu-item');
                    cards.forEach(c => {
                        c.style.border = '1px solid #ddd';
                        c.style.padding = '10px';
                        c.style.marginBottom = '10px';
                        c.style.background = '#fff';
                        c.style.color = '#000';
                    });

                    section.appendChild(contentNode);
                    pdfContainer.appendChild(section);
                }
            };

            // Add Improvement Tips
            const tipsList = document.getElementById('ats-tips-list');
            if (tipsList) {
                const tipsClone = tipsList.cloneNode(true);
                tipsClone.style.color = '#333';
                const listItems = tipsClone.querySelectorAll('li');
                listItems.forEach(li => {
                    li.style.marginBottom = '5px';
                    li.style.color = '#333';
                });
                addSection("Improvement Tips", tipsClone);
            }

            addSection("Skills Profile", skillsSection);

            // Missing Skills
            const missingDiv = document.getElementById('missing-skills-list');
            if (missingDiv) {
                const missingClone = missingDiv.cloneNode(true);
                // Fix pills inside missing clone
                const pills = missingClone.querySelectorAll('.tag');
                pills.forEach(p => {
                    p.style.display = 'inline-block';
                    p.style.border = '1px solid #dbafe5';
                    p.style.padding = '5px 10px';
                    p.style.margin = '2px';
                    p.style.background = '#fdf2ff';
                    p.style.color = '#7000ff';
                });
                addSection("Recommended Skills to Learn", missingClone);
            }

            addSection("Recommended Roles", rolesSection);

            // Container Styles
            pdfContainer.style.width = '100%';
            pdfContainer.style.padding = '40px';
            pdfContainer.style.background = '#fff';
            pdfContainer.style.fontFamily = 'Helvetica, sans-serif';
            pdfContainer.style.boxSizing = 'border-box';

            const opt = {
                margin: 0.4,
                filename: 'Career_Analysis_Report.pdf',
                image: { type: 'jpeg', quality: 0.98 },
                html2canvas: { scale: 2, scrollY: 0, useCORS: true },
                jsPDF: { unit: 'in', format: 'letter', orientation: 'portrait' }
            };

            html2pdf().set(opt).from(pdfContainer).save();
        });
    }
});
