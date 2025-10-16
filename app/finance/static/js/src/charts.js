document.addEventListener("DOMContentLoaded", function () {
  const chartDataElement = document.getElementById("chart-data");
  if (!chartDataElement) {
    return;
  }

  const chartData = JSON.parse(chartDataElement.textContent);
  const unallocatedData = chartData.unallocatedIncome;
  const distributionData = chartData.budgetDistribution;

  function initializeCharts() {
    if (window.innerWidth >= 768) {
      initializeUnallocatedIncomeChart(unallocatedData);
      initializeBudgetDistributionChart(distributionData);
    }
  }

  initializeCharts();

  window.addEventListener("resize", function () {
    initializeCharts();
  });
});

function initializeUnallocatedIncomeChart(data) {
  const canvas = document.getElementById("unallocatedIncomeChart");
  if (!canvas) {
    return;
  }

  const totalIncome = parseFloat(data.totalIncome);
  const totalAllocated = parseFloat(data.totalAllocated);
  const totalCarriedOver = parseFloat(data.totalCarriedOver || 0);
  const unallocated = parseFloat(data.unallocated);

  const totalAvailable = totalIncome + totalCarriedOver;
  const allocatedAmount = Math.min(totalAllocated, totalAvailable);
  const unallocatedAmount = Math.max(0, unallocated);

  const centerTextPlugin = {
    id: "centerText",
    afterDatasetsDraw(chart) {
      const { ctx, chartArea } = chart;
      const centerX = (chartArea.left + chartArea.right) / 2;
      const centerY = (chartArea.top + chartArea.bottom) / 2;

      ctx.save();
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";

      ctx.font = "bold 14px sans-serif";
      ctx.fillStyle = "#6c757d";
      ctx.fillText("Unallocated", centerX, centerY - 15);

      ctx.font = "bold 24px sans-serif";
      ctx.fillStyle = "#333";
      const formattedAmount =
        "$" +
        unallocatedAmount.toLocaleString(undefined, {
          minimumFractionDigits: 2,
          maximumFractionDigits: 2,
        });
      ctx.fillText(formattedAmount, centerX, centerY + 15);

      ctx.restore();
    },
  };

  new Chart(canvas, {
    type: "doughnut",
    data: {
      labels: ["Allocated", "Unallocated"],
      datasets: [
        {
          data: [allocatedAmount, unallocatedAmount],
          backgroundColor: ["#96A78D", "#e9ecef"],
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
              const percentage = ((value / totalAvailable) * 100).toFixed(1);
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
    plugins: [centerTextPlugin],
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
    Need: "#FFC7A7",
    Want: "#F08787",
    Debts: "#F8FAB4",
    Savings: "#96A78D",
    Investing: "#B6CEB4",
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
