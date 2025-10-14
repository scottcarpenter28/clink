document.addEventListener("DOMContentLoaded", function () {
  const tableSelector = document.getElementById("table-selector");
  const columnSelector = document.getElementById("column-selector");

  function getCurrentMonth() {
    const now = new Date();
    const months = [
      "jan",
      "feb",
      "mar",
      "apr",
      "may",
      "jun",
      "jul",
      "aug",
      "sep",
      "oct",
      "nov",
      "dec",
    ];
    return months[now.getMonth()];
  }

  function setDefaultColumn() {
    const currentMonth = getCurrentMonth();
    if (columnSelector) {
      columnSelector.value = currentMonth;
    }
  }

  function updateActiveTable(selectedTable) {
    const allTables = document.querySelectorAll("[data-table]");

    if (allTables.length === 0) {
      console.warn("No tables found with data-table attribute");
      return;
    }

    allTables.forEach((table) => {
      if (table.getAttribute("data-table") === selectedTable) {
        table.classList.add("active-table");
      } else {
        table.classList.remove("active-table");
      }
    });
  }

  function updateActiveColumn(selectedColumn) {
    const allColumns = document.querySelectorAll("[data-column]");

    if (allColumns.length === 0) {
      console.warn("No columns found with data-column attribute");
      return;
    }

    allColumns.forEach((column) => {
      if (column.getAttribute("data-column") === selectedColumn) {
        column.classList.add("active-column");
      } else {
        column.classList.remove("active-column");
      }
    });
  }

  function initializeMobileView() {
    const currentMonth = getCurrentMonth();

    if (columnSelector && !columnSelector.value) {
      columnSelector.value = currentMonth;
    }

    const selectedTable = tableSelector
      ? tableSelector.value
      : "type-breakdown";
    const selectedColumn = columnSelector ? columnSelector.value : currentMonth;

    updateActiveTable(selectedTable);
    updateActiveColumn(selectedColumn);
  }

  if (tableSelector) {
    tableSelector.addEventListener("change", function () {
      updateActiveTable(this.value);
    });
  }

  if (columnSelector) {
    columnSelector.addEventListener("change", function () {
      updateActiveColumn(this.value);
    });
  }

  initializeMobileView();
});
