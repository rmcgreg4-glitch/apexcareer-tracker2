document.addEventListener("DOMContentLoaded", () => {
    if (window.lucide) {
        window.lucide.createIcons();
    }

    const jobForm = document.getElementById("job-form");
    const resumeTextarea = document.getElementById("resume_text");
    const searchInput = document.getElementById("application-search");
    const tableBody = document.getElementById("applications-table-body");
    const emptySearchState = document.getElementById("empty-search-state");
    const applicationCount = document.getElementById("application-count");
    const filterChips = Array.from(document.querySelectorAll(".filter-chip"));
    const autoSubmitFields = Array.from(document.querySelectorAll("[data-auto-submit]"));

    if (jobForm) {
        const submitButton = document.getElementById("submit-button");
        const loadingState = document.getElementById("loading-state");

        jobForm.addEventListener("submit", () => {
            if (loadingState) {
                loadingState.classList.remove("hidden");
            }

            if (submitButton) {
                submitButton.disabled = true;
                submitButton.textContent = "Generating...";
                submitButton.style.opacity = "0.7";
                submitButton.style.cursor = "wait";
            }
        });
    }

    if (searchInput && tableBody) {
        const rows = Array.from(tableBody.querySelectorAll("tr"));
        const totalRows = rows.length;
        const activeChip = document.querySelector(".filter-chip.active");
        let activeFilter = activeChip ? activeChip.dataset.filter || "all" : "all";

        const updateApplicationResults = () => {
            const query = searchInput.value.trim().toLowerCase();
            let visibleCount = 0;

            rows.forEach((row) => {
                const haystack = row.dataset.search || "";
                const status = row.dataset.status || "";
                const matchesQuery = haystack.includes(query);
                const matchesFilter = activeFilter === "all" || status === activeFilter;
                const isVisible = matchesQuery && matchesFilter;

                row.classList.toggle("hidden", !isVisible);

                if (isVisible) {
                    visibleCount += 1;
                }
            });

            if (applicationCount) {
                const isFiltered = query || activeFilter !== "all";
                applicationCount.textContent = isFiltered
                    ? `${visibleCount} of ${totalRows} shown`
                    : `${totalRows} total`;
            }

            if (emptySearchState) {
                emptySearchState.classList.toggle("hidden", visibleCount !== 0);
            }
        };

        searchInput.addEventListener("input", updateApplicationResults);

        filterChips.forEach((chip) => {
            chip.addEventListener("click", () => {
                filterChips.forEach((button) => button.classList.remove("active"));
                chip.classList.add("active");
                activeFilter = chip.dataset.filter || "all";
                updateApplicationResults();
            });
        });

        updateApplicationResults();
    }

    if (resumeTextarea) {
        resumeTextarea.addEventListener("input", () => {
            resumeTextarea.style.borderColor = resumeTextarea.value.trim()
                ? "rgba(249, 115, 22, 0.45)"
                : "";
        });
    }

    autoSubmitFields.forEach((field) => {
        field.addEventListener("change", () => {
            const form = field.closest("form");
            if (form) {
                form.submit();
            }
        });
    });

    const toolCards = Array.from(document.querySelectorAll(".interactive-tool-card"));
    const toolResponseArea = document.getElementById("tool-response-area");
    const toolWorkspaceTitle = document.getElementById("tool-workspace-title");
    const toolWorkspaceDescription = document.getElementById("tool-workspace-description");
    const toolPrimaryInput = document.getElementById("tool-primary-input");
    const toolSecondaryInput = document.getElementById("tool-secondary-input");
    const toolSendButton = document.getElementById("tool-send-button");

    const toolConfigs = {
        "resume-analyzer": {
            placeholder: "Paste your resume and ask what to improve or emphasize...",
            secondaryPlaceholder: "",
            showSecondary: false,
            generateResponse: (primary) => {
                const keywords = extractKeywords(primary);
                const strongest = keywords.slice(0, 3).join(", ") || "your technical and leadership experience";

                return [
                    "Resume review:",
                    `Your resume appears strongest around ${strongest}.`,
                    "Add more measurable outcomes, stronger action verbs, and clearer role-specific positioning.",
                    "If you are targeting internships, highlight ownership, collaboration, and impact in student or project work.",
                ].join("\n");
            },
        },
        "interview-prep": {
            placeholder: "Paste a job description to generate interview preparation questions...",
            secondaryPlaceholder: "",
            showSecondary: false,
            generateResponse: (primary) => {
                const keywords = extractKeywords(primary);
                const focus = keywords[0] || "the core responsibilities";
                const questions = [
                    `How have you applied ${focus} in a real project or internship?`,
                    "Describe a time you solved a difficult problem with limited guidance.",
                    "How do you prioritize work when balancing multiple deadlines?",
                    "Tell me about a time you collaborated across functions or teams.",
                    "What excites you most about this role and why are you a fit?",
                ];

                return `Interview prep questions:\n- ${questions.join("\n- ")}`;
            },
        },
        "follow-up-email": {
            placeholder: "Describe the application or interview situation you want to follow up on...",
            secondaryPlaceholder: "",
            showSecondary: false,
            generateResponse: (primary) => {
                const cleaned = primary.trim() || "the recent interview";

                return [
                    "Follow-up email draft:",
                    "",
                    "Subject: Thank You And Follow-Up",
                    "",
                    "Hello Hiring Team,",
                    "",
                    `Thank you again for the opportunity to discuss ${cleaned}. I enjoyed learning more about the role and the team.`,
                    "I remain very interested in the position and would be glad to provide any additional information that may be helpful.",
                    "",
                    "Best regards,",
                    "[Your Name]",
                ].join("\n");
            },
        },
        "job-match": {
            placeholder: "Paste your resume here...",
            secondaryPlaceholder: "Paste the job description here...",
            showSecondary: true,
            generateResponse: (primary, secondary) => {
                const resumeKeywords = extractKeywords(primary);
                const jobKeywords = extractKeywords(secondary);
                const matched = jobKeywords.filter((keyword) => resumeKeywords.includes(keyword));
                const missing = jobKeywords.filter((keyword) => !resumeKeywords.includes(keyword));
                const score = jobKeywords.length
                    ? Math.round((matched.length / jobKeywords.length) * 100)
                    : 0;

                return [
                    `Match score: ${score}/100`,
                    "",
                    `Strengths: ${matched.slice(0, 4).join(", ") || "Relevant background is present, but needs clearer tailoring."}`,
                    `Skill gaps: ${missing.slice(0, 4).join(", ") || "No major keyword gaps detected."}`,
                    "",
                    "Suggestion: Align your bullet points more directly to the role's top priorities and quantify outcomes where possible.",
                ].join("\n");
            },
        },
    };

    let activeTool = "resume-analyzer";

    const renderChatMessage = (content, type) => {
        if (!toolResponseArea) {
            return;
        }

        const wrapper = document.createElement("div");
        wrapper.className = `chat-message ${type}-message`;

        const title = document.createElement("strong");
        title.textContent = type === "user" ? "You" : "ApexCareer Assistant";

        const body = document.createElement("p");
        body.textContent = content;

        wrapper.appendChild(title);
        wrapper.appendChild(body);
        toolResponseArea.appendChild(wrapper);
        toolResponseArea.scrollTop = toolResponseArea.scrollHeight;
    };

    const updateToolWorkspace = (toolKey) => {
        const config = toolConfigs[toolKey];
        if (!config || !toolWorkspaceTitle || !toolWorkspaceDescription || !toolPrimaryInput || !toolSecondaryInput) {
            return;
        }

        activeTool = toolKey;
        toolCards.forEach((card) => {
            card.classList.toggle("active", card.dataset.tool === toolKey);
        });

        const activeCard = toolCards.find((card) => card.dataset.tool === toolKey);
        toolWorkspaceTitle.textContent = activeCard?.dataset.title || "AI Tool";
        toolWorkspaceDescription.textContent = activeCard?.dataset.description || "";
        toolPrimaryInput.placeholder = config.placeholder;
        toolSecondaryInput.placeholder = config.secondaryPlaceholder;
        toolSecondaryInput.classList.toggle("hidden", !config.showSecondary);
        toolPrimaryInput.value = "";
        toolSecondaryInput.value = "";
        toolResponseArea.innerHTML = "";
        renderChatMessage(activeCard?.dataset.description || "", "ai");
    };

    if (toolCards.length) {
        toolCards.forEach((card) => {
            card.addEventListener("click", () => updateToolWorkspace(card.dataset.tool));
        });

        updateToolWorkspace(activeTool);
    }

    if (toolSendButton && toolPrimaryInput && toolResponseArea) {
        toolSendButton.addEventListener("click", () => {
            const config = toolConfigs[activeTool];
            const primary = toolPrimaryInput.value.trim();
            const secondary = toolSecondaryInput?.value.trim() || "";

            if (!primary) {
                renderChatMessage("Paste some content first so I can help with this tool.", "ai");
                return;
            }

            if (config.showSecondary && !secondary) {
                renderChatMessage("For Job Match Score, paste both your resume and the job description.", "ai");
                return;
            }

            renderChatMessage(primary, "user");
            const response = config.generateResponse(primary, secondary);
            renderChatMessage(response, "ai");
        });
    }

    const chartContainers = Array.from(document.querySelectorAll(".bar-chart"));
    chartContainers.forEach((container) => {
        const rawData = container.dataset.chart;
        if (!rawData) {
            return;
        }

        let chartData = [];
        try {
            chartData = JSON.parse(rawData);
        } catch (error) {
            return;
        }

        renderBarChart(container, chartData);
    });
});

function extractKeywords(text) {
    return Array.from(
        new Set(
            (text.toLowerCase().match(/\b[a-z][a-z0-9+#.-]{2,}\b/g) || [])
                .filter((word) => !COMMON_WORDS.has(word))
        )
    ).slice(0, 12);
}

const COMMON_WORDS = new Set([
    "the", "and", "for", "with", "this", "that", "from", "have", "your", "about",
    "into", "role", "job", "skills", "skill", "work", "team", "years", "experience",
    "using", "used", "need", "needs", "want", "will", "able", "more", "than", "when",
    "where", "their", "they", "them", "been", "were", "what", "which", "while", "also",
]);

function renderBarChart(container, data) {
    if (!data.length) {
        container.innerHTML = "<p class=\"chart-empty\">Not enough data yet.</p>";
        return;
    }

    const maxValue = Math.max(...data.map((item) => item.value), 1);
    container.innerHTML = "";

    data.forEach((item) => {
        const row = document.createElement("div");
        row.className = "chart-row";

        const label = document.createElement("span");
        label.className = "chart-label";
        label.textContent = item.label;

        const barTrack = document.createElement("div");
        barTrack.className = "chart-track";

        const bar = document.createElement("div");
        bar.className = "chart-bar";
        bar.style.width = `${(item.value / maxValue) * 100}%`;
        bar.textContent = item.value;

        barTrack.appendChild(bar);
        row.appendChild(label);
        row.appendChild(barTrack);
        container.appendChild(row);
    });
}
