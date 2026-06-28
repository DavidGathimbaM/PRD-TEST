let selectedClientId = null;
let selectedClientData = null;

const moneyFormatter = new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0
});

function money(value) {
    const number = Number(value || 0);
    return moneyFormatter.format(number);
}

function getElement(id) {
    return document.getElementById(id);
}

function setText(id, value) {
    const element = getElement(id);
    if (element) {
        element.textContent = value;
    }
}

function setValue(id, value) {
    const element = getElement(id);
    if (element) {
        element.value = value ?? "";
    }
}

function numberValue(id) {
    const element = getElement(id);
    if (!element) return 0;
    return Number(element.value || 0);
}

function textValue(id) {
    const element = getElement(id);
    if (!element) return "";
    return element.value || "";
}

function openAddClientModal() {
    const modal = getElement("addClientModal");
    if (modal) {
        modal.classList.remove("hidden");
    }
}

function closeAddClientModal() {
    const modal = getElement("addClientModal");
    const form = getElement("addClientForm");

    if (modal) {
        modal.classList.add("hidden");
    }

    if (form) {
        form.reset();
        setValue("newMonthlyInflow", 0);
        setValue("newMonthlyOutflow", 0);
        setValue("newPrivateReserveBalance", 0);
        setValue("newInvestmentAccountBalance", 0);
        setValue("newInsuranceDeductibles", 0);
        setValue("newFloorAmount", 1000);
        setValue("newTrustValue", 0);
    }
}

function collectNewClientPayload() {
    return {
        householdName: textValue("newHouseholdName"),
        trustName: textValue("newTrustName"),

        client1Name: textValue("newClient1Name"),
        client1Dob: textValue("newClient1Dob"),
        client1Age: numberValue("newClient1Age"),
        client1SsnLast4: textValue("newClient1SsnLast4"),

        client2Name: textValue("newClient2Name"),
        client2Dob: textValue("newClient2Dob"),
        client2Age: numberValue("newClient2Age"),
        client2SsnLast4: textValue("newClient2SsnLast4"),

        monthlyInflow: numberValue("newMonthlyInflow"),
        monthlyOutflow: numberValue("newMonthlyOutflow"),
        privateReserveBalance: numberValue("newPrivateReserveBalance"),
        investmentAccountBalance: numberValue("newInvestmentAccountBalance"),
        insuranceDeductibles: numberValue("newInsuranceDeductibles"),
        floorAmount: numberValue("newFloorAmount"),
        trustValue: numberValue("newTrustValue")
    };
}

async function submitNewClient(event) {
    event.preventDefault();

    const payload = collectNewClientPayload();

    if (!payload.householdName.trim()) {
        alert("Household name is required.");
        return;
    }

    if (!payload.client1Name.trim()) {
        alert("Client 1 name is required.");
        return;
    }

    try {
        const response = await fetch("/api/clients", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        });

        const result = await response.json();

        if (!response.ok) {
            alert(result.error || "Failed to create client.");
            return;
        }

        closeAddClientModal();
        await loadClients();

        if (result.clientId) {
            await loadClientDetail(result.clientId);
        }

        alert("Client created successfully.");
    } catch (error) {
        console.error("Create client failed:", error);
        alert("Failed to create client. Check the Flask terminal.");
    }
}

async function loadClients() {
    try {
        const response = await fetch("/api/clients");
        const clients = await response.json();

        setText("clientCount", clients.length);

        const clientList = getElement("clientList");
        const clientSelect = getElement("clientSelect");

        if (clientList) clientList.innerHTML = "";
        if (clientSelect) clientSelect.innerHTML = "";

        if (!clients.length) {
            if (clientList) {
                clientList.innerHTML = `<p class="muted">No clients found.</p>`;
            }

            if (clientSelect) {
                clientSelect.innerHTML = `<option value="">No clients found</option>`;
            }

            return;
        }

        clients.forEach((client) => {
            if (clientList) {
                const card = document.createElement("div");
                card.className = "client-card";
                card.dataset.clientId = client.id;

                card.innerHTML = `
                    <strong>${client.household_name}</strong>
                    <span>${client.client1_name}${client.client2_name ? " & " + client.client2_name : ""}</span>
                    <span>Inflow: ${money(client.monthly_inflow)} / Outflow: ${money(client.monthly_outflow)}</span>
                `;

                card.addEventListener("click", () => {
                    if (clientSelect) {
                        clientSelect.value = client.id;
                    }
                    loadClientDetail(client.id);
                });

                clientList.appendChild(card);
            }

            if (clientSelect) {
                const option = document.createElement("option");
                option.value = client.id;
                option.textContent = client.household_name;
                clientSelect.appendChild(option);
            }
        });

        if (clientSelect) {
            clientSelect.addEventListener("change", (event) => {
                if (event.target.value) {
                    loadClientDetail(event.target.value);
                }
            });
        }

        if (!selectedClientId && clients.length > 0) {
            if (clientSelect) {
                clientSelect.value = clients[0].id;
            }
            await loadClientDetail(clients[0].id);
        }
    } catch (error) {
        console.error("Failed to load clients:", error);
        alert("Failed to load clients. Check Flask server logs.");
    }
}

async function loadClientDetail(clientId) {
    try {
        selectedClientId = Number(clientId);

        document.querySelectorAll(".client-card").forEach((card) => {
            card.classList.toggle(
                "active",
                Number(card.dataset.clientId) === Number(clientId)
            );
        });

        const clientSelect = getElement("clientSelect");
        if (clientSelect) {
            clientSelect.value = clientId;
        }

        const response = await fetch(`/api/clients/${clientId}`);
        selectedClientData = await response.json();

        if (selectedClientData.error) {
            alert(selectedClientData.error);
            return;
        }

        const client = selectedClientData.client;

        setText("householdTitle", client.household_name);
        setText(
            "householdSubtitle",
            "Client data loaded from SQLite. Quarterly balances can be reviewed and edited before report generation."
        );

        setValue("client1Name", client.client1_name || "");
        setValue("client1Dob", client.client1_dob || "");
        setValue("client1Age", client.client1_age || "");
        setValue("client1SsnLast4", client.client1_ssn_last4 || "");

        setValue("client2Name", client.client2_name || "");
        setValue("client2Dob", client.client2_dob || "");
        setValue("client2Age", client.client2_age || "");
        setValue("client2SsnLast4", client.client2_ssn_last4 || "");

        setValue("inflow", client.monthly_inflow || 0);
        setValue("outflow", client.monthly_outflow || 0);
        setValue("privateReserveBalance", client.private_reserve_balance || 0);
        setValue("investmentAccountBalance", client.investment_account_balance || 0);
        setValue("insuranceDeductibles", client.insurance_deductibles || 0);
        setValue("floorAmount", client.floor_amount || 1000);
        setValue("trustValue", client.trust_value || 0);

        setValue(
            "reportDate",
            new Date().toLocaleDateString("en-US", {
                year: "numeric",
                month: "long",
                day: "numeric"
            })
        );

        renderAccounts();
        renderLiabilities();
        updateCalculations();

        const downloadBtn = getElement("downloadPdfBtn");
        if (downloadBtn) {
            downloadBtn.disabled = false;
        }
    } catch (error) {
        console.error("Failed to load client detail:", error);
        alert("Failed to load client detail. Check Flask server logs.");
    }
}

function renderAccounts() {
    const accounts = selectedClientData?.accounts || [];
    const wrapper = getElement("accountsTable");

    if (!wrapper) return;

    if (!accounts.length) {
        wrapper.innerHTML = `<p class="muted">No accounts found.</p>`;
        return;
    }

    wrapper.innerHTML = `
        <table>
            <thead>
                <tr>
                    <th>Owner</th>
                    <th>Category</th>
                    <th>Type</th>
                    <th>Balance</th>
                </tr>
            </thead>
            <tbody>
                ${accounts.map(account => `
                    <tr>
                        <td>${account.owner}</td>
                        <td>${account.category}</td>
                        <td>${account.account_type}</td>
                        <td>${money(account.balance)}</td>
                    </tr>
                `).join("")}
            </tbody>
        </table>
    `;
}

function renderLiabilities() {
    const liabilities = selectedClientData?.liabilities || [];
    const wrapper = getElement("liabilitiesTable");

    if (!wrapper) return;

    if (!liabilities.length) {
        wrapper.innerHTML = `<p class="muted">No liabilities found.</p>`;
        return;
    }

    wrapper.innerHTML = `
        <table>
            <thead>
                <tr>
                    <th>Type</th>
                    <th>Rate</th>
                    <th>Balance</th>
                </tr>
            </thead>
            <tbody>
                ${liabilities.map(liability => `
                    <tr>
                        <td>${liability.liability_type}</td>
                        <td>${liability.interest_rate}</td>
                        <td>${money(liability.remaining_balance)}</td>
                    </tr>
                `).join("")}
            </tbody>
        </table>
    `;
}

function calculateTotals() {
    const accounts = selectedClientData?.accounts || [];
    const liabilities = selectedClientData?.liabilities || [];

    const inflow = numberValue("inflow");
    const outflow = numberValue("outflow");
    const insuranceDeductibles = numberValue("insuranceDeductibles");
    const trustValue = numberValue("trustValue");

    const automatedTransfer = inflow - outflow;
    const privateReserveTarget = (6 * outflow) + insuranceDeductibles;

    const client1RetirementTotal = accounts
        .filter(account => account.owner === "client1" && account.category === "retirement")
        .reduce((sum, account) => sum + Number(account.balance || 0), 0);

    const client2RetirementTotal = accounts
        .filter(account => account.owner === "client2" && account.category === "retirement")
        .reduce((sum, account) => sum + Number(account.balance || 0), 0);

    const nonRetirementTotal = accounts
        .filter(account => account.category === "non_retirement")
        .reduce((sum, account) => sum + Number(account.balance || 0), 0);

    const liabilitiesTotal = liabilities
        .reduce((sum, liability) => sum + Number(liability.remaining_balance || 0), 0);

    const grandTotalNetWorth =
        client1RetirementTotal +
        client2RetirementTotal +
        nonRetirementTotal +
        trustValue;

    return {
        inflow,
        outflow,
        automatedTransfer,
        privateReserveTarget,
        client1RetirementTotal,
        client2RetirementTotal,
        nonRetirementTotal,
        trustValue,
        liabilitiesTotal,
        grandTotalNetWorth
    };
}

function updateCalculations() {
    if (!selectedClientData) return;

    const totals = calculateTotals();

    const floorAmount = numberValue("floorAmount");
    const privateReserveBalance = numberValue("privateReserveBalance");
    const investmentAccountBalance = numberValue("investmentAccountBalance");
    const insuranceDeductibles = numberValue("insuranceDeductibles");
    const reserveGap = privateReserveBalance - totals.privateReserveTarget;

    setText("automatedTransfer", money(totals.automatedTransfer));
    setText("privateReserveTarget", money(totals.privateReserveTarget));
    setText("grandTotalNetWorth", money(totals.grandTotalNetWorth));
    setText("liabilitiesTotal", money(totals.liabilitiesTotal));

    setText("previewInflow", money(totals.inflow));
    setText("previewOutflow", money(totals.outflow));
    setText("previewOutflowArrow", `X = ${money(totals.outflow)}/month`);
    setText("previewReserveArrow", `${money(totals.automatedTransfer)}/mo`);
    setText("previewReserve", money(totals.automatedTransfer));
    setText("previewFloor1", `${money(floorAmount)} Floor`);
    setText("previewFloor2", `${money(floorAmount)} Floor`);

    const salaryBreakdown = getElement("salaryBreakdown");
    if (salaryBreakdown) {
        const client1SalaryApprox = totals.inflow * 0.53;
        const client2SalaryApprox = totals.inflow * 0.47;

        salaryBreakdown.innerHTML = `
            <span>${money(client1SalaryApprox)} - Client 1</span><br>
            <span>${money(client2SalaryApprox)} - Client 2</span>
        `;
    }

    setText("page2PrivateReserveBalance", money(privateReserveBalance));
    setText("page2InvestmentBalance", `${money(investmentAccountBalance)}+`);
    setText("page2MonthlyOutflow", money(totals.outflow));
    setText("page2Deductibles", money(insuranceDeductibles));
    setText("page2ReserveTarget", money(totals.privateReserveTarget));
    setText("page2ReserveGap", money(reserveGap));

    setText("previewTccName", selectedClientData.client.household_name);
    setText("previewGrandTotal", money(totals.grandTotalNetWorth));
    setText("client1RetirementTotal", money(totals.client1RetirementTotal));
    setText("client2RetirementTotal", money(totals.client2RetirementTotal));
    setText("nonRetirementTotal", money(totals.nonRetirementTotal));
    setText("previewTrustValue", money(totals.trustValue));
    setText("previewLiabilitiesTotal", money(totals.liabilitiesTotal));

    setText("previewClient1", textValue("client1Name"));
    setText(
        "previewClient1Info",
        `Age ${textValue("client1Age")} / DOB ${textValue("client1Dob")} / SSN ${textValue("client1SsnLast4")}`
    );

    setText("previewClient2", textValue("client2Name"));
    setText(
        "previewClient2Info",
        `Age ${textValue("client2Age")} / DOB ${textValue("client2Dob")} / SSN ${textValue("client2SsnLast4")}`
    );

    renderTccAccountBubbles();
}

function renderTccAccountBubbles() {
    const accounts = selectedClientData?.accounts || [];
    const wrapper = getElement("tccAccountBubbles");

    if (!wrapper) return;

    wrapper.innerHTML = accounts.slice(0, 8).map(account => `
        <div class="account-bubble">
            <strong>${account.account_type}</strong>
            <span>${money(account.balance)}</span>
            <small>a/o ${account.as_of_date || "N/A"}</small>
        </div>
    `).join("");
}

function collectReportPayload() {
    const totals = calculateTotals();

    return {
        clientId: selectedClientId,
        householdName: selectedClientData.client.household_name,
        reportDate: textValue("reportDate"),

        client1Name: textValue("client1Name"),
        client1Dob: textValue("client1Dob"),
        client1Age: textValue("client1Age"),
        client1SsnLast4: textValue("client1SsnLast4"),

        client2Name: textValue("client2Name"),
        client2Dob: textValue("client2Dob"),
        client2Age: textValue("client2Age"),
        client2SsnLast4: textValue("client2SsnLast4"),

        inflow: totals.inflow,
        outflow: totals.outflow,
        automatedTransfer: totals.automatedTransfer,

        privateReserveBalance: numberValue("privateReserveBalance"),
        investmentAccountBalance: numberValue("investmentAccountBalance"),
        insuranceDeductibles: numberValue("insuranceDeductibles"),
        floorAmount: numberValue("floorAmount"),
        privateReserveTarget: totals.privateReserveTarget,

        client1RetirementTotal: totals.client1RetirementTotal,
        client2RetirementTotal: totals.client2RetirementTotal,
        nonRetirementTotal: totals.nonRetirementTotal,
        trustValue: totals.trustValue,
        liabilitiesTotal: totals.liabilitiesTotal,
        grandTotalNetWorth: totals.grandTotalNetWorth,

        accounts: selectedClientData.accounts || [],
        liabilities: selectedClientData.liabilities || []
    };
}

async function downloadPdf() {
    if (!selectedClientData) {
        alert("Please select a client first.");
        return;
    }

    try {
        const payload = collectReportPayload();

        const response = await fetch("/api/generate-pdf", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            const errorText = await response.text();
            console.error("PDF generation failed:", errorText);
            alert("PDF generation failed. Check the Flask terminal for the backend error.");
            return;
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);

        const link = document.createElement("a");
        link.href = url;
        link.download = "aw-client-sacs-tcc-report.pdf";
        document.body.appendChild(link);
        link.click();

        link.remove();
        window.URL.revokeObjectURL(url);
    } catch (error) {
        console.error("PDF download error:", error);
        alert("PDF download failed. Check the browser console.");
    }
}

document.addEventListener("DOMContentLoaded", () => {
    loadClients();

    [
        "client1Name",
        "client1Dob",
        "client1Age",
        "client1SsnLast4",
        "client2Name",
        "client2Dob",
        "client2Age",
        "client2SsnLast4",
        "inflow",
        "outflow",
        "privateReserveBalance",
        "investmentAccountBalance",
        "insuranceDeductibles",
        "floorAmount",
        "trustValue",
        "reportDate"
    ].forEach((id) => {
        const element = getElement(id);
        if (element) {
            element.addEventListener("input", updateCalculations);
        }
    });

    const downloadBtn = getElement("downloadPdfBtn");
    if (downloadBtn) {
        downloadBtn.addEventListener("click", downloadPdf);
    }

    const openAddClientBtn = getElement("openAddClientBtn");
    if (openAddClientBtn) {
        openAddClientBtn.addEventListener("click", openAddClientModal);
    }

    const closeAddClientBtn = getElement("closeAddClientBtn");
    if (closeAddClientBtn) {
        closeAddClientBtn.addEventListener("click", closeAddClientModal);
    }

    const cancelAddClientBtn = getElement("cancelAddClientBtn");
    if (cancelAddClientBtn) {
        cancelAddClientBtn.addEventListener("click", closeAddClientModal);
    }

    const addClientForm = getElement("addClientForm");
    if (addClientForm) {
        addClientForm.addEventListener("submit", submitNewClient);
    }

    const addClientModal = getElement("addClientModal");
    if (addClientModal) {
        addClientModal.addEventListener("click", (event) => {
            if (event.target === addClientModal) {
                closeAddClientModal();
            }
        });
    }
});