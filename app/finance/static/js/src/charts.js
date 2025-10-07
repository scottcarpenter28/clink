document.addEventListener("DOMContentLoaded", function () {
  const chartDataElement = document.getElementById("chart-data");
  if (!chartDataElement) {
    return;
  }

  const chartData = JSON.parse(chartDataElement.textContent);
  const unallocatedData = chartData.unallocatedIncome;
  const distributionData = chartData.budgetDistribution;

  initializeUnallocatedIncomeChart(unallocatedData);
  initializeBudgetDistributionChart(distributionData);
});

function initializeUnallocatedIncomeChart(data) {
  const canvas = document.getElementById("unallocatedIncomeChart");
  if (!canvas) {
    return;
  }

  const totalIncome = parseFloat(data.totalIncome);
  const totalAllocated = parseFloat(data.totalAllocated);
  const unallocated = parseFloat(data.unallocated);

  const allocatedAmount = Math.min(totalAllocated, totalIncome);
  const unallocatedAmount = Math.max(0, unallocated);

  new Chart(canvas, {
    type: "doughnut",
    data: {
      labels: ["Allocated", "Unallocated"],
      datasets: [
        {
          data: [allocatedAmount, unallocatedAmount],
          backgroundColor: ["#28a745", "#e9ecef"],
          borderWidth: 2,
          borderColor: "#fff",
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        tooltip: {
          callbacks: {
            label: function (context) {
              const label = context.label || "";
              const value = context.parsed;
              const percentage = ((value / totalIncome) * 100).toFixed(1);
              return (
                label +
                ": $" +
                value.toLocaleString(undefined, {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                }) +
                " (" +
                percentage +
                "%)"
              );
            },
          },
        },
        legend: {
          display: true,
          position: "bottom",
        },
      },
    },
  });
}

function initializeBudgetDistributionChart(data) {
  const canvas = document.getElementById("budgetDistributionChart");
  if (!canvas) {
    return;
  }

  const labels = Object.keys(data);
  const values = Object.values(data).map((v) => parseFloat(v));

  if (labels.length === 0 || values.every((v) => v === 0)) {
    canvas.style.display = "none";
    const container = canvas.parentElement;
    const message = document.createElement("p");
    message.className = "empty-state";
    message.textContent = "No budgets allocated yet";
    container.appendChild(message);
    return;
  }

  const colorMap = {
    Need: "#ff6b6b",
    Want: "#a29bfe",
    Debts: "#8b4513",
    Savings: "#4dabf7",
    Investing: "#51cf66",
  };

  const backgroundColors = labels.map((label) => colorMap[label] || "#6c757d");

  new Chart(canvas, {
    type: "pie",
    data: {
      labels: labels,
      datasets: [
        {
          data: values,
          backgroundColor: backgroundColors,
          borderWidth: 2,
          borderColor: "#fff",
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        tooltip: {
          callbacks: {
            label: function (context) {
              const label = context.label || "";
              const value = context.parsed;
              const total = context.dataset.data.reduce((a, b) => a + b, 0);
              const percentage = ((value / total) * 100).toFixed(1);
              return (
                label +
                ": $" +
                value.toLocaleString(undefined, {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                }) +
                " (" +
                percentage +
                "%)"
              );
            },
          },
        },
        legend: {
          display: true,
          position: "bottom",
        },
      },
    },
  });
}
