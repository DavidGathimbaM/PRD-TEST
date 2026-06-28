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
        element.textContent = value ?? "";
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

function clearElement(element) {
    if (!element) return;
    while (element.firstChild) {
        element.removeChild(element.firstChild);
    }
}

function makeElement(tag, className, text) {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (text !== undefined && text !== null) element.textContent = text;
    return element;
}

function openModal(id) {
    const modal = getElement(id);
    if (modal) modal.classList.remove("hidden");
}

function closeModal(id) {
    const modal = getElement(id);
    if (modal) modal.classList.add("hidden");
}

function openAddClientModal() {
    openModal("addClientModal");
}

function closeAddClientModal() {
    closeModal("addClientModal");
    const form = getElement("addClientForm");

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

function openAddAccountModal() {
    if (!selectedClientId) {
        alert("Please select a client first.");
        return;
    }

    const today = new Date().toLocaleDateString("en-US", {
        year: "numeric",
        month: "2-digit",
        day: "2-digit"
    });

    setValue("newAccountAsOfDate", today);
    openModal("addAccountModal");
}

function closeAddAccountModal() {
    closeModal("addAccountModal");
    const form = getElement("addAccountForm");

    if (form) {
        form.reset();
        setValue("newAccountBalance", 0);
        setValue("newAccountCashBalance", 0);
    }
}

function openAddLiabilityModal() {
    if (!selectedClientId) {
        alert("Please select a client first.");
        return;
    }

    openModal("addLiabilityModal");
}

function closeAddLiabilityModal() {
    closeModal("addLiabilityModal");
    const form = getElement("addLiabilityForm");

    if (form) {
        form.reset();
        setValue("newLiabilityRemainingBalance", 0);
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

function collectNewAccountPayload() {
    return {
        owner: textValue("newAccountOwner"),
        category: textValue("newAccountCategory"),
        accountType: textValue("newAccountType"),
        accountName: textValue("newAccountName"),
        accountLast4: textValue("newAccountLast4"),
        balance: numberValue("newAccountBalance"),
        cashBalance: numberValue("newAccountCashBalance"),
        asOfDate: textValue("newAccountAsOfDate")
    };
}

function collectNewLiabilityPayload() {
    return {
        liabilityType: textValue("newLiabilityType"),
        interestRate: textValue("newLiabilityInterestRate"),
        remainingBalance: numberValue("newLiabilityRemainingBalance")
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
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(payload)
        });

        const result = await response.json();

        if (!response.ok) {
            alert(result.error || "Failed to create client.");
            return;
        }

        closeAddClientModal();
        selectedClientId = result.clientId || null;

        await loadClients();

        if (result.clientId) {
            await loadClientDetail(result.clientId);
        }

        alert("Client created successfully.");
    } catch (error) {
        console.error("Create client failed:", error);
        alert("Failed to create client. Check server logs.");
    }
}

async function submitNewAccount(event) {
    event.preventDefault();

    if (!selectedClientId) {
        alert("Please select a client first.");
        return;
    }

    const payload = collectNewAccountPayload();

    if (!payload.accountType.trim()) {
        alert("Account type is required.");
        return;
    }

    try {
        const response = await fetch(`/api/clients/${selectedClientId}/accounts`, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(payload)
        });

        const result = await response.json();

        if (!response.ok) {
            alert(result.error || "Failed to create account.");
            return;
        }

        closeAddAccountModal();
        await loadClientDetail(selectedClientId);
        alert("Account added successfully.");
    } catch (error) {
        console.error("Create account failed:", error);
        alert("Failed to create account. Check server logs.");
    }
}

async function submitNewLiability(event) {
    event.preventDefault();

    if (!selectedClientId) {
        alert("Please select a client first.");
        return;
    }

    const payload = collectNewLiabilityPayload();

    if (!payload.liabilityType.trim()) {
        alert("Liability type is required.");
        return;
    }

    try {
        const response = await fetch(`/api/clients/${selectedClientId}/liabilities`, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(payload)
        });

        const result = await response.json();

        if (!response.ok) {
            alert(result.error || "Failed to create liability.");
            return;
        }

        closeAddLiabilityModal();
        await loadClientDetail(selectedClientId);
        alert("Liability added successfully.");
    } catch (error) {
        console.error("Create liability failed:", error);
        alert("Failed to create liability. Check server logs.");
    }
}

async function deleteAccount(accountId) {
    if (!confirm("Delete this account?")) return;

    try {
        const response = await fetch(`/api/accounts/${accountId}`, {
            method: "DELETE"
        });

        const result = await response.json();

        if (!response.ok) {
            alert(result.error || "Failed to delete account.");
            return;
        }

        await loadClientDetail(selectedClientId);
    } catch (error) {
        console.error("Delete account failed:", error);
        alert("Failed to delete account. Check server logs.");
    }
}

async function deleteLiability(liabilityId) {
    if (!confirm("Delete this liability?")) return;

    try {
        const response = await fetch(`/api/liabilities/${liabilityId}`, {
            method: "DELETE"
        });

        const result = await response.json();

        if (!response.ok) {
            alert(result.error || "Failed to delete liability.");
            return;
        }

        await loadClientDetail(selectedClientId);
    } catch (error) {
        console.error("Delete liability failed:", error);
        alert("Failed to delete liability. Check server logs.");
    }
}

async function loadClients() {
    try {
        const response = await fetch("/api/clients");
        const clients = await response.json();

        setText("clientCount", clients.length);

        const clientList = getElement("clientList");
        const clientSelect = getElement("clientSelect");

        clearElement(clientList);
        clearElement(clientSelect);

        if (!clients.length) {
            if (clientList) clientList.appendChild(makeElement("p", "muted", "No clients found."));
            if (clientSelect) {
                const option = document.createElement("option");
                option.value = "";
                option.textContent = "No clients found";
                clientSelect.appendChild(option);
            }
            return;
        }

        clients.forEach((client) => {
            if (clientList) {
                const card = makeElement("div", "client-card");
                card.dataset.clientId = client.id;

                card.appendChild(makeElement("strong", null, client.household_name || "Unnamed Client"));
                card.appendChild(makeElement("span", null, `${client.client1_name || ""}${client.client2_name ? " & " + client.client2_name : ""}`));
                card.appendChild(makeElement("span", null, `Inflow: ${money(client.monthly_inflow)} / Outflow: ${money(client.monthly_outflow)}`));

                card.addEventListener("click", () => {
                    if (clientSelect) clientSelect.value = client.id;
                    loadClientDetail(client.id);
                });

                clientList.appendChild(card);
            }

            if (clientSelect) {
                const option = document.createElement("option");
                option.value = client.id;
                option.textContent = client.household_name || "Unnamed Client";
                clientSelect.appendChild(option);
            }
        });

        if (clientSelect) {
            clientSelect.onchange = (event) => {
                if (event.target.value) loadClientDetail(event.target.value);
            };
        }

        const clientToLoad = selectedClientId || clients[0].id;
        if (clientSelect) clientSelect.value = clientToLoad;
        await loadClientDetail(clientToLoad);
    } catch (error) {
        console.error("Failed to load clients:", error);
        alert("Failed to load clients. Check server logs.");
    }
}

async function loadClientDetail(clientId) {
    try {
        selectedClientId = Number(clientId);

        document.querySelectorAll(".client-card").forEach((card) => {
            card.classList.toggle("active", Number(card.dataset.clientId) === Number(clientId));
        });

        const clientSelect = getElement("clientSelect");
        if (clientSelect) clientSelect.value = clientId;

        const response = await fetch(`/api/clients/${clientId}`);
        selectedClientData = await response.json();

        if (selectedClientData.error) {
            alert(selectedClientData.error);
            return;
        }

        const client = selectedClientData.client;

        setText("householdTitle", client.household_name || "Unnamed Client");
        setText("householdSubtitle", "Client data loaded from SQLite. Quarterly balances can be reviewed and edited before report generation.");

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

        setValue("reportDate", new Date().toLocaleDateString("en-US", {
            year: "numeric",
            month: "long",
            day: "numeric"
        }));

        renderAccounts();
        renderLiabilities();
        updateCalculations();

        const downloadBtn = getElement("downloadPdfBtn");
        if (downloadBtn) downloadBtn.disabled = false;
    } catch (error) {
        console.error("Failed to load client detail:", error);
        alert("Failed to load client detail. Check server logs.");
    }
}

function renderAccounts() {
    const accounts = selectedClientData?.accounts || [];
    const wrapper = getElement("accountsTable");
    if (!wrapper) return;

    clearElement(wrapper);

    if (!accounts.length) {
        wrapper.appendChild(makeElement("p", "muted", "No accounts found."));
        return;
    }

    const table = document.createElement("table");
    const thead = document.createElement("thead");
    const headerRow = document.createElement("tr");

    ["Owner", "Category", "Type", "Balance", "Action"].forEach((header) => {
        const th = document.createElement("th");
        th.textContent = header;
        headerRow.appendChild(th);
    });

    thead.appendChild(headerRow);
    table.appendChild(thead);

    const tbody = document.createElement("tbody");

    accounts.forEach((account) => {
        const row = document.createElement("tr");

        [
            account.owner || "",
            account.category || "",
            account.account_type || "",
            money(account.balance)
        ].forEach((value) => {
            const td = document.createElement("td");
            td.textContent = value;
            row.appendChild(td);
        });

        const actionTd = document.createElement("td");
        const deleteBtn = makeElement("button", "danger-link", "Delete");
        deleteBtn.type = "button";
        deleteBtn.addEventListener("click", () => deleteAccount(account.id));
        actionTd.appendChild(deleteBtn);
        row.appendChild(actionTd);

        tbody.appendChild(row);
    });

    table.appendChild(tbody);
    wrapper.appendChild(table);
}

function renderLiabilities() {
    const liabilities = selectedClientData?.liabilities || [];
    const wrapper = getElement("liabilitiesTable");
    if (!wrapper) return;

    clearElement(wrapper);

    if (!liabilities.length) {
        wrapper.appendChild(makeElement("p", "muted", "No liabilities found."));
        return;
    }

    const table = document.createElement("table");
    const thead = document.createElement("thead");
    const headerRow = document.createElement("tr");

    ["Type", "Rate", "Balance", "Action"].forEach((header) => {
        const th = document.createElement("th");
        th.textContent = header;
        headerRow.appendChild(th);
    });

    thead.appendChild(headerRow);
    table.appendChild(thead);

    const tbody = document.createElement("tbody");

    liabilities.forEach((liability) => {
        const row = document.createElement("tr");

        [
            liability.liability_type || "",
            liability.interest_rate || "",
            money(liability.remaining_balance)
        ].forEach((value) => {
            const td = document.createElement("td");
            td.textContent = value;
            row.appendChild(td);
        });

        const actionTd = document.createElement("td");
        const deleteBtn = makeElement("button", "danger-link", "Delete");
        deleteBtn.type = "button";
        deleteBtn.addEventListener("click", () => deleteLiability(liability.id));
        actionTd.appendChild(deleteBtn);
        row.appendChild(actionTd);

        tbody.appendChild(row);
    });

    table.appendChild(tbody);
    wrapper.appendChild(table);
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

    const grandTotalNetWorth = client1RetirementTotal + client2RetirementTotal + nonRetirementTotal + trustValue;

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
        clearElement(salaryBreakdown);
        salaryBreakdown.appendChild(makeElement("span", null, `${money(totals.inflow * 0.53)} - Client 1`));
        salaryBreakdown.appendChild(document.createElement("br"));
        salaryBreakdown.appendChild(makeElement("span", null, `${money(totals.inflow * 0.47)} - Client 2`));
    }

    setText("page2PrivateReserveBalance", money(privateReserveBalance));
    setText("page2InvestmentBalance", `${money(investmentAccountBalance)}+`);
    setText("page2MonthlyOutflow", money(totals.outflow));
    setText("page2Deductibles", money(insuranceDeductibles));
    setText("page2ReserveTarget", money(totals.privateReserveTarget));
    setText("page2ReserveGap", money(reserveGap));

    setText("previewTccName", selectedClientData.client.household_name || "Unnamed Client");
    setText("previewGrandTotal", money(totals.grandTotalNetWorth));
    setText("client1RetirementTotal", money(totals.client1RetirementTotal));
    setText("client2RetirementTotal", money(totals.client2RetirementTotal));
    setText("nonRetirementTotal", money(totals.nonRetirementTotal));
    setText("previewTrustValue", money(totals.trustValue));
    setText("previewLiabilitiesTotal", money(totals.liabilitiesTotal));

    setText("previewClient1", textValue("client1Name"));
    setText("previewClient1Info", `Age ${textValue("client1Age")} / DOB ${textValue("client1Dob")} / SSN ${textValue("client1SsnLast4")}`);

    setText("previewClient2", textValue("client2Name"));
    setText("previewClient2Info", `Age ${textValue("client2Age")} / DOB ${textValue("client2Dob")} / SSN ${textValue("client2SsnLast4")}`);

    renderTccAccountBubbles();
}

function renderTccAccountBubbles() {
    const accounts = selectedClientData?.accounts || [];
    const wrapper = getElement("tccAccountBubbles");
    if (!wrapper) return;

    clearElement(wrapper);

    accounts.slice(0, 8).forEach((account) => {
        const bubble = makeElement("div", "account-bubble");
        bubble.appendChild(makeElement("strong", null, account.account_type || "Account"));
        bubble.appendChild(makeElement("span", null, money(account.balance)));
        bubble.appendChild(makeElement("small", null, `a/o ${account.as_of_date || "N/A"}`));
        wrapper.appendChild(bubble);
    });
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
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            const errorText = await response.text();
            console.error("PDF generation failed:", errorText);
            alert("PDF generation failed. Check server logs.");
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
        alert("PDF download failed. Check browser console.");
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
        if (element) element.addEventListener("input", updateCalculations);
    });

    const handlers = [
        ["downloadPdfBtn", downloadPdf],
        ["openAddClientBtn", openAddClientModal],
        ["closeAddClientBtn", closeAddClientModal],
        ["cancelAddClientBtn", closeAddClientModal],
        ["openAddAccountBtn", openAddAccountModal],
        ["closeAddAccountBtn", closeAddAccountModal],
        ["cancelAddAccountBtn", closeAddAccountModal],
        ["openAddLiabilityBtn", openAddLiabilityModal],
        ["closeAddLiabilityBtn", closeAddLiabilityModal],
        ["cancelAddLiabilityBtn", closeAddLiabilityModal]
    ];

    handlers.forEach(([id, handler]) => {
        const element = getElement(id);
        if (element) element.addEventListener("click", handler);
    });

    const addClientForm = getElement("addClientForm");
    if (addClientForm) addClientForm.addEventListener("submit", submitNewClient);

    const addAccountForm = getElement("addAccountForm");
    if (addAccountForm) addAccountForm.addEventListener("submit", submitNewAccount);

    const addLiabilityForm = getElement("addLiabilityForm");
    if (addLiabilityForm) addLiabilityForm.addEventListener("submit", submitNewLiability);

    ["addClientModal", "addAccountModal", "addLiabilityModal"].forEach((modalId) => {
        const modal = getElement(modalId);
        if (modal) {
            modal.addEventListener("click", (event) => {
                if (event.target === modal) closeModal(modalId);
            });
        }
    });
});