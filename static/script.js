let expenses = [];

// ------------------ ADD EXPENSE ------------------
function addExpense() {
    const data = {
        category: document.getElementById("category").value,
        amount: document.getElementById("amount").value,
        date: document.getElementById("date").value,
        note: document.getElementById("note").value
    };

    fetch("/api/add_expense", {
        method: "POST",
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
    })
    .then(() => {
        alert("Expense Added");
        document.getElementById("category").value = "";
        document.getElementById("amount").value = "";
        document.getElementById("date").value = "";
        document.getElementById("note").value = "";
    });
}

// ------------------ LOAD EXPENSES ------------------
function loadExpenses() {
    fetch("/api/get_expenses")
    .then(res => res.json())
    .then(data => {
        expenses = data;
        loadTable(expenses);
        calculateSummary(expenses);
        loadCharts(expenses);
        loadPrediction();
    });
}

// ------------------ BUILD TABLE ------------------
function loadTable(data) {
    let table = `
        <tr>
            <th>ID</th>
            <th>Category</th>
            <th>Amount</th>
            <th>Date</th>
            <th>Note</th>
            <th>Delete</th>
        </tr>
    `;

    data.forEach(e => {
        table += `
            <tr>
                <td>${e.id}</td>
                <td>${e.category}</td>
                <td>${e.amount}</td>
                <td>${e.date}</td>
                <td>${e.note}</td>
                <td><button class="btn btn-danger btn-sm" onclick="deleteExpense(${e.id})">Delete</button></td>
            </tr>
        `;
    });

    document.getElementById("table").innerHTML = table;
}

// ------------------ DELETE EXPENSE ------------------
function deleteExpense(id) {
    fetch("/api/delete/" + id, { method: "DELETE" })
    .then(() => {
        loadExpenses();
    });
}

// ------------------ SEARCH FILTER ------------------
function searchExpenses() {
    let input = document.getElementById("searchInput").value.toLowerCase();
    let rows = document.querySelectorAll("#table tr");

    rows.forEach(row => {
        if (row.innerText.toLowerCase().includes(input)) {
            row.style.display = "";
        } else {
            row.style.display = "none";
        }
    });
}

// ------------------ SORT FUNCTIONS ------------------
function sortAmountLow() {
    expenses.sort((a, b) => a.amount - b.amount);
    loadTable(expenses);
}

function sortAmountHigh() {
    expenses.sort((a, b) => b.amount - a.amount);
    loadTable(expenses);
}

function sortDateRecent() {
    expenses.sort((a, b) => new Date(b.date) - new Date(a.date));
    loadTable(expenses);
}

function sortDateOld() {
    expenses.sort((a, b) => new Date(a.date) - new Date(b.date));
    loadTable(expenses);
}

// ------------------ SUMMARY CARDS ------------------
function calculateSummary(expenses) {
    let today = new Date().toISOString().split("T")[0];
    let month = today.slice(0, 7);

    let todayTotal = 0;
    let monthTotal = 0;
    let categoryTotals = {};

    expenses.forEach(e => {
        if (e.date === today) todayTotal += parseFloat(e.amount);
        if (e.date.startsWith(month)) monthTotal += parseFloat(e.amount);

        if (!categoryTotals[e.category]) categoryTotals[e.category] = 0;
        categoryTotals[e.category] += parseFloat(e.amount);
    });

    let highestCategory = Object.keys(categoryTotals).sort((a, b) => categoryTotals[b] - categoryTotals[a])[0] || "-";
    let avgSpend = (monthTotal / 30).toFixed(2);

    document.getElementById("todayTotal").innerText = "₹" + todayTotal;
    document.getElementById("monthTotal").innerText = "₹" + monthTotal;
    document.getElementById("highCat").innerText = highestCategory;
    document.getElementById("avgSpend").innerText = "₹" + avgSpend;
}

// ------------------ GRAPHS ------------------
function loadCharts(expenses) {
    fetch("/api/graph_data")
    .then(res => res.json())
    .then(graph => {

        // Pie Chart
        new Chart(document.getElementById("pieChart"), {
            type: "pie",
            data: {
                labels: graph.categoryLabels,
                datasets: [{ data: graph.categoryTotals }]
            }
        });

        // Bar Chart
        new Chart(document.getElementById("barChart"), {
            type: "bar",
            data: {
                labels: graph.dateLabels,
                datasets: [{ data: graph.dateTotals }]
            }
        });
    });
}

// ------------------ AI PREDICTION ------------------
async function loadPrediction() {
    let res = await fetch("/api/predict");
    let data = await res.json();

    document.getElementById("predictValue").innerText = "₹" + data.prediction;
}

// ------------------ AUTO LOAD ON VIEW PAGE ------------------
window.onload = function() {
    if (location.pathname === "/view") {
        loadExpenses();
    }
};
