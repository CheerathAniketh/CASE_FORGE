/* =========================================================
   CASEFORGE FRONTEND
   Connects the Figma UI to the existing FastAPI backend
========================================================= */


/* =========================================================
   CONFIGURATION
========================================================= */

const API_BASE = "http://localhost:8000/api/v1";

const USER_ID = 1;

let selectedComplexity = "beginner";

let currentCases = [];


/* =========================================================
   DOM HELPERS
========================================================= */

function $(id) {
    return document.getElementById(id);
}


/* =========================================================
   TOAST
========================================================= */

function showToast(message) {

    const toast = $("toast");

    toast.textContent = message;

    toast.classList.remove("hidden");

    setTimeout(() => {
        toast.classList.add("hidden");
    }, 3000);
}



/* =========================================================
   NAVIGATION
========================================================= */



/*
 * EVENT DELEGATION
 */

document.addEventListener("click", function(event) {

    const navItem = event.target.closest(
        ".nav-item[data-page]"
    );

    const pageButton = event.target.closest(
        ".text-button[data-page]"
    );

    if (navItem) {

        event.preventDefault();

        const pageName = navItem.dataset.page;

        navigateTo(pageName);

        return;
    }

    if (pageButton) {

        event.preventDefault();

        const pageName = pageButton.dataset.page;

        navigateTo(pageName);

    }

});

/* Sidebar navigation */

/* =========================================================
   NAVIGATION
========================================================= */

function navigateTo(pageName) {

    console.log("Navigating to:", pageName);

    // Hide every page
    document.querySelectorAll(".page").forEach(page => {
        page.classList.remove("active-page");
    });

    // Show requested page
    const targetPage = document.getElementById(`${pageName}Page`);

    if (!targetPage) {
        console.error(`Page not found: ${pageName}Page`);
        return;
    }

    targetPage.classList.add("active-page");

    // Update sidebar active state
    document.querySelectorAll(".nav-item").forEach(item => {
        item.classList.remove("active");
    });

    const activeNav = document.querySelector(
        `.nav-item[data-page="${pageName}"]`
    );

    if (activeNav) {
        activeNav.classList.add("active");
    }

    // Load history when opening history
    if (pageName === "history") {
        loadHistory();
    }

    window.scrollTo({
        top: 0,
        behavior: "smooth"
    });
}


/* Sidebar navigation */

document.querySelectorAll(".nav-item[data-page]").forEach(item => {

    item.addEventListener("click", function (event) {

        event.preventDefault();
        event.stopPropagation();

        const page = this.dataset.page;

        navigateTo(page);

    });

});


/* Other navigation buttons such as View All */

document.querySelectorAll(
    ".text-button[data-page]"
).forEach(button => {

    button.addEventListener("click", function (event) {

        event.preventDefault();

        navigateTo(this.dataset.page);

    });

});

/* Quick forge */

$("quickForgeBtn").addEventListener("click", () => {

    navigateTo("dashboard");

    setTimeout(() => {

        $("industry").focus();

    }, 200);

});


/* Solve case */

$("solveCaseBtn").addEventListener("click", () => {

    const caseId = $("generatedCase").dataset.caseId;

    if (caseId) {
        $("evaluationCaseId").value = caseId;
    }

    navigateTo("evaluate");

});


/* =========================================================
   DIFFICULTY SELECTOR
========================================================= */

document.querySelectorAll(".difficulty").forEach(button => {

    button.addEventListener("click", () => {

        document.querySelectorAll(".difficulty").forEach(btn => {
            btn.classList.remove("active");
        });

        button.classList.add("active");

        selectedComplexity = button.dataset.value;

    });

});


/* =========================================================
   API REQUEST HELPER
========================================================= */

async function apiRequest(url, options = {}) {

    const response = await fetch(url, {
        ...options,

        headers: {
            "Content-Type": "application/json",
            ...(options.headers || {})
        }
    });


    let data;

    try {
        data = await response.json();
    }

    catch {
        data = {};
    }


    if (!response.ok) {

        const message =
            data.detail ||
            data.message ||
            "Something went wrong with the server.";

        throw new Error(message);

    }


    return data;
}


/* =========================================================
   GENERATE CASE
========================================================= */

$("generateBtn").addEventListener("click", generateCase);


async function generateCase() {

    const button = $("generateBtn");

    const industry = $("industry").value;

    const focusArea = $("focusArea").value.trim();

    const timeLimit =
        parseInt($("timeLimit").value, 10) || 60;


    if (!focusArea) {

        showToast("Please enter a focus area.");

        $("focusArea").focus();

        return;
    }


    button.disabled = true;

    button.textContent = "Generating... ⏳";


    try {

        showToast("AI is generating your case...");


        const payload = {

            user_id: USER_ID,

            industry: industry,

            complexity: selectedComplexity,

            focus_area: focusArea,

            time_limit: timeLimit

        };


        /*
         * REAL BACKEND ENDPOINT
         *
         * POST /api/v1/cases/generate
         */

        const data = await apiRequest(
            `${API_BASE}/cases/generate`,
            {
                method: "POST",

                body: JSON.stringify(payload)
            }
        );


        displayGeneratedCase(data);


        showToast("Case generated successfully!");


        await loadHistory();

    }

    catch (error) {

        console.error("Generation error:", error);

        showToast(`Generation failed: ${error.message}`);

    }

    finally {

        button.disabled = false;

        button.textContent = "⚡ Forge Case Study";

    }

}


/* =========================================================
   DISPLAY GENERATED CASE
========================================================= */

function displayGeneratedCase(data) {

    const container = $("generatedCase");

    const caseData = data.case_data || {};


    $("caseTitle").textContent =
        data.title || "Generated Case";


    $("caseIndustry").textContent =
        data.industry || "Unknown Industry";


    $("caseComplexity").textContent =
        capitalize(data.complexity || selectedComplexity);


    /*
     * Different generated cases may have slightly different
     * field names. We safely check several possibilities.
     */

    const scenario =
        caseData.scenario_overview ||
        caseData.scenario ||
        caseData.description ||
        "No scenario overview was returned.";


    $("caseScenario").textContent = scenario;


    const questions =
        caseData.discussion_questions ||
        caseData.questions ||
        [];


    const questionsList = $("discussionQuestions");

    questionsList.innerHTML = "";


    if (questions.length === 0) {

        const li = document.createElement("li");

        li.textContent =
            "No discussion questions were returned.";

        questionsList.appendChild(li);

    }

    else {

        questions.forEach(question => {

            const li = document.createElement("li");

            li.textContent = question;

            questionsList.appendChild(li);

        });

    }


    /*
     * Save the generated case ID so
     * "Solve This Case" knows which case to evaluate.
     */

    container.dataset.caseId =
        data.case_id || "";


    container.classList.remove("hidden");


    container.scrollIntoView({
        behavior: "smooth",
        block: "start"
    });

}


/* =========================================================
   EVALUATE SOLUTION
========================================================= */

$("evaluateBtn").addEventListener("click", evaluateSolution);


async function evaluateSolution(event) {
    event.preventDefault();

    const button = $("evaluateBtn");

    const caseId =
        parseInt($("evaluationCaseId").value, 10);


    const solution =
        $("solutionInput").value.trim();


    if (!caseId || caseId < 1) {

        showToast("Please enter a valid Case ID.");

        return;
    }


    if (!solution) {

        showToast("Please enter your solution.");

        $("solutionInput").focus();

        return;
    }


    button.disabled = true;

    button.textContent = "Evaluating... ⏳";


    $("evaluationLoading").classList.remove("hidden");

    $("evaluationResults").classList.add("hidden");


    try {

        const payload = {

            user_id: USER_ID,

            case_id: caseId,

            solution: solution

        };


        /*
         * REAL BACKEND ENDPOINT
         *
         * POST /api/v1/solutions/evaluate
         */

        const data = await apiRequest(
            `${API_BASE}/solutions/evaluate`,
            {
                method: "POST",

                body: JSON.stringify(payload)
            }
        );


        displayEvaluation(data);


        showToast("Evaluation completed!");


    }

    catch (error) {

        console.error("Evaluation error:", error);

        showToast(`Evaluation failed: ${error.message}`);

    }

    finally {

        button.disabled = false;

        button.textContent = "⚡ Submit for Evaluation";

        $("evaluationLoading").classList.add("hidden");

    }

}


/* =========================================================
   DISPLAY EVALUATION
========================================================= */

function displayEvaluation(data) {

    const scores = data.scores || {};

    const feedback = data.feedback || {};


    $("overallScore").textContent =
        formatScore(scores.overall);


    $("problemScore").textContent =
        formatScore(scores.problem_understanding);


    $("analyticalScore").textContent =
        formatScore(scores.analytical_rigor);


    $("businessScore").textContent =
        formatScore(scores.business_acumen);


    $("communicationScore").textContent =
        formatScore(scores.communication);


    $("feasibilityScore").textContent =
        formatScore(scores.feasibility);


    fillList(
        "strengthsList",
        feedback.strengths
    );


    fillList(
        "weaknessesList",
        feedback.weaknesses
    );


    fillList(
        "suggestionsList",
        feedback.suggestions
    );


    $("evaluationResults").classList.remove("hidden");


    $("evaluationResults").scrollIntoView({
        behavior: "smooth",
        block: "start"
    });

}


/* =========================================================
   HISTORY
========================================================= */

async function loadHistory() {

    try {

        const data = await apiRequest(
            `${API_BASE}/users/${USER_ID}/cases`,
            {
                method: "GET"
            }
        );


        currentCases = data.cases || [];


        updateDashboardMetrics(currentCases);

        renderDashboardHistory(currentCases);

        renderFullHistory(currentCases);

    }

    catch (error) {

        console.error("History error:", error);

        renderHistoryError();

    }

}


/* =========================================================
   DASHBOARD HISTORY
========================================================= */

function renderDashboardHistory(cases) {

    const tbody = $("dashboardHistory");

    tbody.innerHTML = "";


    if (!cases.length) {

        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="empty-row">
                    No cases generated yet. Forge your first case!
                </td>
            </tr>
        `;

        return;
    }


    const recentCases = cases.slice(0, 5);


    recentCases.forEach(item => {

        const row = document.createElement("tr");

        row.innerHTML = `
            <td>${escapeHtml(item.title || "Untitled Case")}</td>

            <td>${escapeHtml(item.industry || "—")}</td>

            <td>${formatDate(item.created_at)}</td>

            <td>${capitalize(item.complexity || "—")}</td>

            <td>
                <span class="status-badge">
                    Completed
                </span>
            </td>
        `;

        tbody.appendChild(row);

    });

}


/* =========================================================
   FULL HISTORY
========================================================= */

function renderFullHistory(cases) {

    const tbody = $("historyTableBody");

    tbody.innerHTML = "";


    if (!cases.length) {

        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="empty-row">
                    No case history available.
                </td>
            </tr>
        `;

        return;
    }


    cases.forEach(item => {

        const row = document.createElement("tr");

        row.innerHTML = `
            <td>#${item.id ?? "—"}</td>

            <td>${escapeHtml(item.title || "Untitled Case")}</td>

            <td>${escapeHtml(item.industry || "—")}</td>

            <td>${capitalize(item.complexity || "—")}</td>

            <td>${formatDate(item.created_at)}</td>
        `;

        tbody.appendChild(row);

    });

}


/* =========================================================
   METRICS
========================================================= */

function updateDashboardMetrics(cases) {

    $("casesForged").textContent =
        cases.length;


    $("analyticsCases").textContent =
        cases.length;


    /*
     * The currently documented history endpoint
     * provides cases, not evaluation statistics.
     *
     * Therefore we don't invent an average score.
     */

    if (cases.length) {

        const industries = {};

        cases.forEach(item => {

            const industry =
                item.industry || "Unknown";

            industries[industry] =
                (industries[industry] || 0) + 1;

        });


        const mostCommonIndustry =
            Object.entries(industries)
                .sort((a, b) => b[1] - a[1])[0];


        if (mostCommonIndustry) {

            $("targetIndustry").textContent =
                mostCommonIndustry[0];

        }

    }

}


/* =========================================================
   REFRESH HISTORY
========================================================= */

$("refreshHistoryBtn").addEventListener(
    "click",
    async () => {

        showToast("Refreshing case history...");

        await loadHistory();

        showToast("History updated.");

    }
);


/* =========================================================
   SEARCH
========================================================= */

$("searchInput").addEventListener(
    "input",
    event => {

        const query =
            event.target.value
                .toLowerCase()
                .trim();


        if (!query) {

            renderDashboardHistory(currentCases);

            return;
        }


        const filtered =
            currentCases.filter(item => {

                return (

                    String(item.title || "")
                        .toLowerCase()
                        .includes(query)

                    ||

                    String(item.industry || "")
                        .toLowerCase()
                        .includes(query)

                    ||

                    String(item.complexity || "")
                        .toLowerCase()
                        .includes(query)

                );

            });


        renderDashboardHistory(filtered);

    }
);


/* =========================================================
   LOGOUT
========================================================= */

$("logoutBtn").addEventListener(
    "click",
    () => {

        showToast(
            "Logout will be connected when authentication is added."
        );

    }
);


/* =========================================================
   HELPERS
========================================================= */

function fillList(elementId, items) {

    const list = $(elementId);

    list.innerHTML = "";


    if (!Array.isArray(items) || items.length === 0) {

        const li = document.createElement("li");

        li.textContent = "No feedback available.";

        list.appendChild(li);

        return;
    }


    items.forEach(item => {

        const li = document.createElement("li");

        li.textContent = item;

        list.appendChild(li);

    });

}


function formatScore(score) {

    if (score === undefined || score === null) {
        return "—";
    }

    return score;

}


function capitalize(value) {

    if (!value) {
        return "";
    }

    return value.charAt(0).toUpperCase() +
        value.slice(1);

}


function formatDate(dateString) {

    if (!dateString) {
        return "—";
    }


    const date = new Date(dateString);


    if (Number.isNaN(date.getTime())) {
        return dateString;
    }


    return date.toLocaleDateString(
        "en-IN",
        {
            day: "2-digit",
            month: "short",
            year: "numeric"
        }
    );

}


/*
 * Prevent case titles returned from the API
 * from being interpreted as HTML.
 */

function escapeHtml(value) {

    const div = document.createElement("div");

    div.textContent = value;

    return div.innerHTML;

}


/* =========================================================
   INITIAL LOAD
========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    () => {

        console.log("CaseForge frontend initialized.");

        console.log(
            "Backend:",
            API_BASE
        );


        loadHistory();

    }
);