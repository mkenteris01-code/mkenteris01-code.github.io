document.addEventListener('DOMContentLoaded', () => {
    let allData = [];
    let currentIndex = 0;
    let filteredData = [];

    const dom = {
        loading: document.getElementById('loading'),
        card: document.getElementById('descriptor-card'),
        level: document.getElementById('level-badge'),
        id: document.getElementById('id-badge'),
        flag: document.getElementById('flag-badge'),
        text: document.getElementById('descriptor-text'),
        assigned: document.getElementById('assigned-category'),
        evidence: document.getElementById('evidence-text'),
        issueType: document.getElementById('issue-type'),

        form: document.getElementById('validation-form'),
        decision: document.getElementById('decision'),
        newCat: document.getElementById('new-category'),
        confidence: document.querySelectorAll('input[name="confidence"]'),
        notes: document.getElementById('notes'),

        saveBtn: document.getElementById('save-btn'),
        prevBtn: document.getElementById('prev-btn'),
        nextBtn: document.getElementById('next-btn'),
        statusMsg: document.getElementById('status-msg'),

        progressText: document.getElementById('progress-text'),
        progressBar: document.getElementById('progress-bar-fill'),

        filterFlagged: document.getElementById('filter-flagged-only')
    };

    // Load Data
    fetch('/api/data')
        .then(response => response.json())
        .then(data => {
            allData = data;
            // Add custom index to keep track
            allData.forEach((item, index) => item.originalIndex = index);

            // Initial filter
            updateFilter();

            dom.loading.classList.add('hidden');
            if (filteredData.length > 0) {
                dom.card.classList.remove('hidden');
                loadItem(currentIndex);
            } else {
                dom.statusMsg.textContent = "No data found.";
            }
        })
        .catch(err => {
            dom.loading.textContent = "Error loading data: " + err;
        });

    // Event Listeners
    dom.form.addEventListener('submit', (e) => {
        e.preventDefault();
        saveCurrent();
    });

    dom.prevBtn.addEventListener('click', () => {
        if (currentIndex > 0) {
            currentIndex--;
            loadItem(currentIndex);
        }
    });

    dom.nextBtn.addEventListener('click', () => {
        // Just skip without saving
        if (currentIndex < filteredData.length - 1) {
            currentIndex++;
            loadItem(currentIndex);
        }
    });

    dom.filterFlagged.addEventListener('change', () => {
        updateFilter();
        currentIndex = 0; // Reset to start
        if (filteredData.length > 0) {
            loadItem(currentIndex);
        }
    });

    // Auto-set confidence if "CONFIRM" is selected? (Optional UI sugar)

    function updateFilter() {
        const onlyFlagged = dom.filterFlagged.checked;
        if (onlyFlagged) {
            filteredData = allData.filter(d => d.IsFlagged);
        } else {
            filteredData = allData;
        }
        updateProgress();
    }

    function loadItem(index) {
        if (!filteredData[index]) return;

        const item = filteredData[index];

        // Map fields based on standardized API response
        const level = item['Level'];
        const id = item['ID'];
        const text = item['Descriptor'];
        const assigned = item['Category'];
        const isFlagged = item['IsFlagged'];
        const evidence = item['Evidence'];
        const issueType = item['IssueType'];

        // Existing values if any
        const existingDecision = item['ExpertReview'];
        const existingNewCat = item['NewCategory'];
        const existingConf = item['Confidence'];
        const existingNotes = item['Notes'];

        // Render
        dom.level.textContent = level;
        dom.id.textContent = id;
        dom.text.textContent = text;
        dom.assigned.textContent = assigned;
        dom.evidence.textContent = evidence || '-';
        dom.issueType.textContent = issueType || '-';

        if (isFlagged) {
            dom.flag.classList.remove('hidden');
        } else {
            dom.flag.classList.add('hidden');
        }

        // Form Reset / Pre-fill
        dom.decision.value = existingDecision || "";
        dom.newCat.value = existingNewCat || "";
        dom.notes.value = existingNotes || "";

        // Radio buttons
        dom.confidence.forEach(r => r.checked = false);
        if (existingConf) {
            const radio = document.querySelector(`input[name="confidence"][value="${existingConf}"]`);
            if (radio) radio.checked = true;
        }

        // Navigation state
        dom.prevBtn.disabled = index === 0;
        dom.nextBtn.textContent = index === filteredData.length - 1 ? "Finish" : "Skip";
        dom.saveBtn.textContent = index === filteredData.length - 1 ? "Save & Finish" : "Save & Next";

        updateProgress();
        dom.statusMsg.textContent = "";
    }

    function updateProgress() {
        const total = filteredData.length;
        const current = currentIndex + 1;
        dom.progressText.textContent = `${current}/${total}`;
        dom.progressBar.style.width = `${(current / total) * 100}%`;
    }

    function saveCurrent() {
        const item = filteredData[currentIndex];

        const id = item['ID'];
        const level = item['Level'];

        const payload = {
            ID: id,
            Level: level,
            Decision: dom.decision.value,
            NewCategory: dom.newCat.value,
            Confidence: document.querySelector('input[name="confidence"]:checked')?.value,
            Notes: dom.notes.value
        };

        dom.saveBtn.disabled = true;
        dom.saveBtn.textContent = "Saving...";

        fetch('/api/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        })
            .then(res => res.json())
            .then(res => {
                if (res.status === 'success') {
                    // Update local model
                    item['ExpertReview'] = payload.Decision;
                    item['NewCategory'] = payload.NewCategory;
                    item['Confidence'] = payload.Confidence;
                    item['Notes'] = payload.Notes;

                    dom.statusMsg.textContent = "Saved!";
                    setTimeout(() => {
                        if (currentIndex < filteredData.length - 1) {
                            currentIndex++;
                            loadItem(currentIndex);
                        }
                    }, 500);
                } else {
                    alert('Error saving: ' + res.error);
                }
            })
            .finally(() => {
                dom.saveBtn.disabled = false;
            });
    }
});
