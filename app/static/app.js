document.addEventListener("DOMContentLoaded", () => {
    const healthIndicator = document.getElementById("health-indicator");
    const demoScrollBtn = document.getElementById("demo-scroll");
    const authSection = document.getElementById("auth-section");
    const loginForm = document.getElementById("login-form");
    const loginBtn = document.getElementById("login-btn");
    const loginError = document.getElementById("login-error");

    const generateSection = document.getElementById("generate-section");
    const generateForm = document.getElementById("generate-form");
    const generateBtn = document.getElementById("generate-btn");
    const btnText = generateBtn.querySelector(".btn-text");
    const loader = generateBtn.querySelector(".loader");
    const generateError = document.getElementById("generate-error");
    const userDisplay = document.getElementById("user-display");
    const loadingSection = document.getElementById("loading-section");
    const progressStatus = document.getElementById("progress-status");
    const progressSteps = Array.from(document.querySelectorAll(".step"));

    const resultSection = document.getElementById("result-section");
    const caseContent = document.getElementById("case-content");
    const caseMetadata = document.getElementById("case-metadata");
    const newCaseBtn = document.getElementById("new-case-btn");
    const resetBtn = document.getElementById("reset-btn");
    const logoutBtn = document.getElementById("logout-btn");
    const copyJsonBtn = document.getElementById("copy-json-btn");
    const copyTextBtn = document.getElementById("copy-text-btn");
    const exportJsonBtn = document.getElementById("export-json-btn");
    const exportTxtBtn = document.getElementById("export-txt-btn");
    const toastContainer = document.getElementById("toast-container");

    let token = localStorage.getItem("caseforge_token");
    let currentUser = localStorage.getItem("caseforge_user");
    let latestCasePayload = null;

    checkHealth();
    if (token) {
        showGenerateSection();
    }

    if (demoScrollBtn) {
        demoScrollBtn.addEventListener("click", () => {
            document.getElementById("demo").scrollIntoView({ behavior: "smooth" });
        });
    }

    async function checkHealth() {
        try {
            const res = await fetch("/health/detailed");
            if (res.ok) {
                healthIndicator.textContent = "System online";
                healthIndicator.className = "health-status ok";
                return;
            }
            throw new Error("Bad status");
        } catch (e) {
            healthIndicator.textContent = "Backend offline";
            healthIndicator.className = "health-status error";
        }
    }

    loginForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const studentIdInput = document.getElementById("student-id");
        const emailInput = document.getElementById("email");
        const studentId = studentIdInput.value.trim();
        const email = emailInput.value.trim();

        clearValidation(studentIdInput);
        loginError.classList.add("hidden");

        if (studentId.length < 2) {
            markInvalid(studentIdInput, "Student ID is required.");
            loginError.textContent = "Please provide a valid student ID.";
            loginError.classList.remove("hidden");
            return;
        }

        setButtonLoading(loginBtn, true, "Authenticating...");

        try {
            const response = await fetch("/api/v1/auth/login", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ student_id: studentId, email: email || null })
            });

            const data = await response.json();
            if (!response.ok) throw new Error(data.detail || data.error || "Login failed");

            token = data.access_token;
            currentUser = studentId;
            localStorage.setItem("caseforge_token", token);
            localStorage.setItem("caseforge_user", studentId);
            showToast("Login successful", "Authentication confirmed.", "success");
            showGenerateSection();
        } catch (error) {
            loginError.textContent = error.message;
            loginError.classList.remove("hidden");
            showToast("Login failed", error.message, "error");
        } finally {
            setButtonLoading(loginBtn, false, "Authenticate");
        }
    });

    function showGenerateSection() {
        authSection.classList.add("hidden");
        generateSection.classList.remove("hidden");
        userDisplay.textContent = currentUser ? `User: ${currentUser}` : "";
    }

    generateForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        generateError.classList.add("hidden");
        const payload = buildPayload();
        if (!payload) return;

        latestCasePayload = null;
        generateSection.classList.add("hidden");
        loadingSection.classList.remove("hidden");
        startProgressAnimation();

        try {
            const response = await fetch("/api/v1/case-studies/generate", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify(payload)
            });

            const data = await response.json();
            stopProgressAnimation(true);

            if (response.status === 401) {
                localStorage.removeItem("caseforge_token");
                window.location.reload();
                return;
            }

            if (!response.ok) throw new Error(data.detail || data.error || "Generation failed");

            latestCasePayload = data;
            renderCaseResult(data);
            showToast("Case generated", "Workflow completed successfully.", "success");
        } catch (error) {
            stopProgressAnimation(false);
            loadingSection.classList.add("hidden");
            generateSection.classList.remove("hidden");
            generateError.textContent = error.message;
            generateError.classList.remove("hidden");
            showToast("Generation failed", error.message, "error");
        }
    });

    resetBtn.addEventListener("click", () => {
        generateForm.reset();
        document.getElementById("industry").value = "E-commerce";
        document.getElementById("focus-area").value = "Market Expansion";
        clearValidation(document.getElementById("industry"));
        clearValidation(document.getElementById("num-questions"));
        clearValidation(document.getElementById("time-limit"));
        generateError.classList.add("hidden");
        showToast("Form reset", "Default values restored.", "success");
    });

    newCaseBtn.addEventListener("click", () => {
        resultSection.classList.add("hidden");
        generateSection.classList.remove("hidden");
        window.scrollTo({ top: generateSection.offsetTop - 20, behavior: "smooth" });
    });

    if (logoutBtn) {
        logoutBtn.addEventListener("click", () => {
            localStorage.removeItem("caseforge_token");
            localStorage.removeItem("caseforge_user");
            window.location.reload();
        });
    }

    copyJsonBtn.addEventListener("click", () => {
        if (!latestCasePayload) return;
        copyToClipboard(JSON.stringify(latestCasePayload.case_data, null, 2));
        showToast("Copied", "Case JSON copied to clipboard.", "success");
    });

    copyTextBtn.addEventListener("click", () => {
        if (!latestCasePayload) return;
        copyToClipboard(formatCaseText(latestCasePayload.case_data));
        showToast("Copied", "Case text copied to clipboard.", "success");
    });

    exportJsonBtn.addEventListener("click", () => {
        if (!latestCasePayload) return;
        downloadFile(`caseforge_${latestCasePayload.uuid}.json`, JSON.stringify(latestCasePayload.case_data, null, 2));
    });

    exportTxtBtn.addEventListener("click", () => {
        if (!latestCasePayload) return;
        downloadFile(`caseforge_${latestCasePayload.uuid}.txt`, formatCaseText(latestCasePayload.case_data));
    });

    function buildPayload() {
        const industryInput = document.getElementById("industry");
        const questionsInput = document.getElementById("num-questions");
        const timeInput = document.getElementById("time-limit");

        clearValidation(industryInput);
        clearValidation(questionsInput);
        clearValidation(timeInput);

        if (industryInput.value.trim().length < 2) {
            markInvalid(industryInput, "Industry is required.");
            showToast("Validation error", "Please enter a valid industry.", "error");
            return null;
        }

        const numQuestions = parseInt(questionsInput.value, 10);
        if (Number.isNaN(numQuestions) || numQuestions < 1 || numQuestions > 10) {
            markInvalid(questionsInput, "Choose between 1 and 10 questions.");
            showToast("Validation error", "Discussion questions must be between 1 and 10.", "error");
            return null;
        }

        const timeLimit = parseInt(timeInput.value, 10);
        if (Number.isNaN(timeLimit) || timeLimit < 30 || timeLimit > 180) {
            markInvalid(timeInput, "Time limit must be between 30 and 180 minutes.");
            showToast("Validation error", "Time limit must be between 30 and 180 minutes.", "error");
            return null;
        }

        return {
            industry: industryInput.value.trim(),
            complexity: document.getElementById("complexity").value,
            focus_area: document.getElementById("focus-area").value.trim() || null,
            num_questions: numQuestions,
            time_limit_minutes: timeLimit
        };
    }

    function renderCaseResult(data) {
        loadingSection.classList.add("hidden");
        resultSection.classList.remove("hidden");

        const cd = data.case_data;
        caseMetadata.innerHTML = buildMetaCards(data);

        let html = `<h1>${cd.title}</h1>`;
        if (cd.executive_summary) {
            html += `<div class="case-block"><h3>Executive Summary</h3><p>${cd.executive_summary}</p></div>`;
        }

        if (cd.background) {
            html += `<div class="case-block"><h3>Background</h3>
            <p><strong>Company:</strong> ${cd.background.company_name} (Est. ${cd.background.founded_year})</p>
            <p><strong>Context:</strong> ${cd.background.company_context}</p>
            <p><strong>Market:</strong> ${cd.background.market_situation}</p>
            <p><strong>Key Players:</strong> ${cd.background.key_players}</p></div>`;
        }

        html += `<div class="case-block"><h3>Problem Statement</h3><p>${cd.problem_statement}</p></div>`;

        if (cd.current_situation) {
            html += `<div class="case-block"><h3>Current Situation</h3>
            <p><strong>Challenges:</strong> ${cd.current_situation.challenges?.join(", ") || ""}</p>
            <p><strong>Opportunities:</strong> ${cd.current_situation.opportunities?.join(", ") || ""}</p>
            <p><strong>Constraints:</strong> ${cd.current_situation.constraints?.join(", ") || ""}</p></div>`;
        }

        if (cd.financial_data) {
            html += `<div class="case-block"><h3>Financial Data</h3><ul>
                <li>Revenue: $${cd.financial_data.current_revenue_millions}M</li>
                <li>Market Size: $${cd.financial_data.market_size_billions}B</li>
                <li>Growth Rate: ${cd.financial_data.growth_rate_percent}%</li>
                <li>Profit Margin: ${cd.financial_data.profit_margin_percent}%</li>
            </ul></div>`;
        }

        if (cd.discussion_questions?.length) {
            html += `<div class="case-block"><h3>Discussion Questions</h3><ul>`;
            cd.discussion_questions.forEach((q) => {
                html += `<li><strong>${q.focus_area}:</strong> ${q.question}<br><small><em>Hint: ${q.hint}</em></small></li>`;
            });
            html += `</ul></div>`;
        }

        if (cd.solution_framework) {
            html += `<div class="case-block"><h3>Solution Framework</h3>
            <p>${cd.solution_framework.recommended_approach}</p>
            <ul>${(cd.solution_framework.implementation_steps || []).map(step => `<li>${step}</li>`).join("")}</ul>
            <p><strong>Expected outcomes:</strong> ${cd.solution_framework.expected_outcomes}</p>
            <p><strong>Timeline:</strong> ${cd.solution_framework.timeline}</p></div>`;
        }

        if (cd.key_learnings?.length) {
            html += `<div class="case-block"><h3>Key Learnings</h3><ul>`;
            cd.key_learnings.forEach((l) => {
                html += `<li>${l}</li>`;
            });
            html += `</ul></div>`;
        }

        caseContent.innerHTML = html;
    }

    function buildMetaCards(data) {
        const items = [
            { label: "Generation time", value: data.generation_time_ms ? `${data.generation_time_ms} ms` : "-" },
            { label: "Tokens used", value: data.tokens_used ?? "-" },
            { label: "Model", value: data.model_used || "-" },
            { label: "Validation score", value: data.validation_score != null ? data.validation_score.toFixed(2) : "-" },
            { label: "Refinement retries", value: data.refinement_count ?? 0 },
            { label: "Workflow status", value: data.workflow_status || "-" }
        ];

        return items.map(item => {
            return `<div class="meta-card"><div class="meta-label">${item.label}</div><div class="meta-value">${item.value}</div></div>`;
        }).join("");
    }

    function startProgressAnimation() {
        progressSteps.forEach(step => step.classList.remove("done", "active"));
        let stepIndex = 0;
        progressSteps[0].classList.add("active");
        const statusMessages = [
            "Generating initial draft...",
            "Validating structure and quality...",
            "Refining missing sections...",
            "Saving final case study..."
        ];

        progressStatus.textContent = statusMessages[0];
        loadingSection.dataset.interval = setInterval(() => {
            progressSteps[stepIndex].classList.remove("active");
            progressSteps[stepIndex].classList.add("done");
            stepIndex = Math.min(stepIndex + 1, progressSteps.length - 1);
            progressSteps[stepIndex].classList.add("active");
            progressStatus.textContent = statusMessages[stepIndex] || "Finalizing response...";
        }, 1500);
    }

    function stopProgressAnimation(success) {
        const intervalId = loadingSection.dataset.interval;
        if (intervalId) clearInterval(intervalId);
        if (success) {
            progressSteps.forEach(step => {
                step.classList.remove("active");
                step.classList.add("done");
            });
            progressStatus.textContent = "Workflow complete.";
        }
    }

    function setButtonLoading(button, isLoading, label) {
        button.disabled = isLoading;
        const labelNode = button.querySelector("span");
        if (labelNode) labelNode.textContent = label;
        if (button === generateBtn) {
            loader.classList.toggle("hidden", !isLoading);
            btnText.classList.toggle("hidden", isLoading);
        }
    }

    function markInvalid(input, message) {
        input.classList.add("is-invalid");
        input.setAttribute("aria-invalid", "true");
        input.setAttribute("title", message);
    }

    function clearValidation(input) {
        input.classList.remove("is-invalid");
        input.removeAttribute("aria-invalid");
        input.removeAttribute("title");
    }

    function showToast(title, message, type = "success") {
        const toast = document.createElement("div");
        toast.className = `toast ${type}`;
        toast.innerHTML = `<div class="toast-title">${title}</div><div class="toast-body">${message}</div>`;
        toastContainer.appendChild(toast);
        setTimeout(() => toast.remove(), 4000);
    }

    function copyToClipboard(text) {
        navigator.clipboard.writeText(text);
    }

    function downloadFile(filename, content) {
        const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
        const link = document.createElement("a");
        link.href = URL.createObjectURL(blob);
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        link.remove();
        URL.revokeObjectURL(link.href);
        showToast("Export ready", `${filename} downloaded.`, "success");
    }

    function formatCaseText(cd) {
        const parts = [];
        parts.push(`Title: ${cd.title}`);
        parts.push(`Industry: ${cd.industry}`);
        parts.push(`Complexity: ${cd.complexity}`);
        if (cd.executive_summary) parts.push(`\nExecutive Summary:\n${cd.executive_summary}`);
        if (cd.problem_statement) parts.push(`\nProblem Statement:\n${cd.problem_statement}`);
        if (cd.background) {
            parts.push(`\nBackground:\nCompany: ${cd.background.company_name}`);
            parts.push(`Context: ${cd.background.company_context}`);
            parts.push(`Market: ${cd.background.market_situation}`);
            parts.push(`Key Players: ${cd.background.key_players}`);
        }
        if (cd.discussion_questions?.length) {
            parts.push("\nDiscussion Questions:");
            cd.discussion_questions.forEach((q, idx) => {
                parts.push(`${idx + 1}. ${q.question}`);
            });
        }
        if (cd.key_learnings?.length) {
            parts.push("\nKey Learnings:");
            cd.key_learnings.forEach((item, idx) => {
                parts.push(`${idx + 1}. ${item}`);
            });
        }
        return parts.join("\n");
    }
});