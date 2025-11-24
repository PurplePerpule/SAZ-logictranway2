const API = "http://127.0.0.1:5000";

// ======================== ОБНОВЛЕНИЕ ДАННЫХ ========================

async function loadOrders() {
  try {
    const res = await fetch(`${API}/orders`);
    const orders = await res.json();
    const dateFilter = document.getElementById("dateFilter").value;
    const searchFilter = document
      .getElementById("searchFilter")
      .value.toLowerCase();

    const filtered = orders.filter((o) => {
      const dateMatch = !dateFilter || o.created_at.includes(dateFilter);
      const searchMatch =
        !searchFilter ||
        o.vehicle?.driver.toLowerCase().includes(searchFilter) ||
        o.vehicle?.gos_number.toLowerCase().includes(searchFilter);
      return dateMatch && searchMatch;
    });

    const active = filtered.filter((o) => o.status !== "completed");
    const completed = filtered.filter((o) => o.status === "completed");

    renderActiveOrders(active);
    renderHistory(completed);

    // Статистика
    document.getElementById("pendingCount").textContent = active.filter(
      (o) => o.status === "new",
    ).length;
    document.getElementById("inTransitCount").textContent = active.filter(
      (o) => o.status === "assigned",
    ).length;
    document.getElementById("completedToday").textContent = completed.length;
  } catch (err) {
    console.error(err);
  }
}

async function suggestVehicle(orderId) {
  try {
    const res = await fetch(`${API}/suggest_vehicle/${orderId}`);
    const vehicle = await res.json();
    if (vehicle) {
      document.getElementById("vehicleSelect").value = vehicle.id;
      alert(`Рекомендована машина: ${vehicle.gos_number} (${vehicle.driver})`);
    } else {
      alert("Подходящая машина не найдена");
    }
  } catch (e) {
    alert("Ошибка подбора");
  }
}

async function printTTN(orderId) {
  const res = await fetch(`${API}/ttn/${orderId}`);
  const data = await res.json();

  const win = window.open("", "", "height=500, width=800");
  win.document.write(`
    <html>
    <head>
      <title>ТТН #${data.ttn_number}</title>
    </head>
    <body>
      <h1>ТОВАРНО-ТРАНСПОРТНАЯ НАКЛАДНАЯ #${data.ttn_number}</h1>
      <p>Дата: ${data.date}</p>
      <p>Водитель: ${data.driver}</p>
      <p>Гос. номер: ${data.gos_number}</p>
      <p>Общий вес: ${data.total_weight} кг</p>
      <h2>Грузы:</h2>
      <ul>
        ${data.cargos.map((c) => `<li>${c.name} — ${c.weight} кг x ${c.quantity}</li>`).join("")}
      </ul>
      <img src="qrcode.png" alt="QR-код">  # добавь QR-код через библиотеку Qrious
    </body>
    </html>
  `);
  win.document.close();
  win.print();
}

async function loadVehicles() {
  try {
    const res = await fetch(`${API}/vehicles`, {
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
    });
    const vehicles = await res.json();
    renderVehicles(vehicles);
  } catch (err) {
    console.error(err);
  }
}

// ======================== ОТРИСОВКА ТАБЛИЦ ========================

function renderActiveOrders(orders) {
  const tbody = document.querySelector("#ordersTable tbody");
  tbody.innerHTML = "";

  orders.forEach((order) => {
    const tr = document.createElement("tr");
    tr.className = `status-${order.status}`;

    const vehicleInfo = order.vehicle
      ? `${order.vehicle.garage_number} — ${order.vehicle.brand} (${order.vehicle.driver})`
      : "—";

    tr.innerHTML = `
      <td>${order.id}</td>
      <td>${new Date(order.created_at).toLocaleString("ru-RU")}</td>
      <td>${order.cargos.length}</td>
      <td>${getStatusText(order.status)}</td>
      <td>${vehicleInfo}</td>
      <td>
        ${
          order.status === "new"
            ? `<button class="btn" onclick="openAssignModal(${order.id})">Подобрать машину</button>`
            : ""
        }
        ${
          order.status === "assigned"
            ? `<button class="btn" onclick="completeOrder(${order.id})">Завершить рейс</button>`
            : ""
        }
        <button class="btn" onclick="viewOrderDetails(${order.id})">Подробно</button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

function renderVehicles(vehicles) {
  const tbody = document.querySelector("#vehiclesTable tbody");
  tbody.innerHTML = "";

  vehicles.forEach((v) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${v.garage_number}</td>
      <td>${v.brand}</td>
      <td>${v.driver}</td>
      <td><span class="status-badge ${v.status === "free" ? "status-free" : "status-busy"}">
        ${v.status === "free" ? "Свободна" : "Занята"}
      </span></td>
    `;
    tbody.appendChild(tr);
  });
}

function renderHistory(orders) {
  const tbody = document.querySelector("#historyTable tbody");
  tbody.innerHTML = "";

  orders.forEach((order) => {
    const vehicle = order.vehicle
      ? `${order.vehicle.garage_number} — ${order.vehicle.brand}`
      : "—";

    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${order.id}</td>
      <td>${new Date(order.created_at).toLocaleString("ru-RU")}</td>
      <td>${vehicle}</td>
      <td>${order.cargos.length}</td>
    `;
    tbody.appendChild(tr);
  });
}

// ======================== МОДАЛЬНОЕ ОКНО ДЛЯ ПОДБОРА МАШИНЫ ========================

let currentOrderId = null;

function openAssignModal(orderId) {
  currentOrderId = orderId;
  fetch(`${API}/orders/${orderId}`)
    .then((r) => r.json())
    .then((order) => {
      document.getElementById("modalOrderId").textContent = order.id;
      document.getElementById("modalCargoCount").textContent =
        order.cargos.length;

      // Подгружаем свободные машины
      fetch(`${API}/vehicles`)
        .then((r) => r.json())
        .then((vehicles) => {
          const freeVehicles = vehicles.filter((v) => v.status === "free");
          const select = document.getElementById("vehicleSelect");
          select.innerHTML = '<option value="">— Выберите машину —</option>';
          freeVehicles.forEach((v) => {
            const opt = document.createElement("option");
            opt.value = v.id;
            opt.textContent = `${v.garage_number} — ${v.brand} (${v.driver}) — ${v.capacity} кг`;
            select.appendChild(opt);
          });
        });
    });

  document.getElementById("assignModal").style.display = "block";
}

function closeAssignModal() {
  document.getElementById("assignModal").style.display = "none";
  currentOrderId = null;
}

async function assignVehicle() {
  const vehicleId = document.getElementById("vehicleSelect").value;
  if (!vehicleId || !currentOrderId) return alert("Выберите машину");

  try {
    const res = await fetch(`${API}/orders/${currentOrderId}/assign`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ vehicle_id: parseInt(vehicleId) }),
    });

    if (res.ok) {
      alert("Машина успешно назначена!");
      closeAssignModal();
      loadOrders();
      loadVehicles();
    } else {
      const err = await res.json();
      alert("Ошибка: " + (err.error || "неизвестно"));
    }
  } catch (e) {
    alert("Ошибка связи с сервером");
  }
}

// ======================== ЗАВЕРШЕНИЕ РЕЙСА ========================

async function completeOrder(orderId) {
  if (!confirm("Завершить рейс и освободить машину?")) return;

  try {
    const res = await fetch(`${API}/orders/${orderId}/complete`, {
      method: "POST",
    });

    if (res.ok) {
      alert("Рейс завершён, машина освобождена");
      loadOrders();
      loadVehicles();
    }
  } catch (e) {
    alert("Ошибка");
  }
}

// ======================== ПОДРОБНОСТИ ЗАЯВКИ ========================

function viewOrderDetails(orderId) {
  fetch(`${API}/orders/${orderId}`)
    .then((r) => r.json())
    .then((order) => {
      let cargosHtml = "";
      order.cargos.forEach((c) => {
        cargosHtml += `<li>${c.name} — ${c.weight}кг ×${c.quantity}, ${c.length}×${c.width}×${c.height}м, ${c.departure} → ${c.destination}</li>`;
      });

      const vehicle = order.vehicle
        ? `${order.vehicle.garage_number} — ${order.vehicle.brand} (${order.vehicle.driver})`
        : "Не назначена";

      alert(
        `
ЗАЯВКА #${order.id}
Создано: ${new Date(order.created_at).toLocaleString("ru-RU")}
Статус: ${getStatusText(order.status)}
Машина: ${vehicle}

Грузы:
${cargosHtml}
      `.trim(),
      );
    });
}

// ======================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ========================

let lastNewCount = 0;

setInterval(() => {
  fetch(`${API}/orders`)
    .then((r) => r.json())
    .then((orders) => {
      const newCount = orders.filter((o) => o.status === "new").length;
      if (newCount > lastNewCount) {
        document.getElementById("notifySound").play();
      }
      lastNewCount = newCount;
    });
}, 5000);

function getStatusText(status) {
  switch (status) {
    case "new":
      return "Новая";
    case "assigned":
      return "Машина назначена";
    case "completed":
      return "Завершён";
    default:
      return status;
  }
}

// ======================== ТАБЫ ========================

function showTab(tabId) {
  document
    .querySelectorAll(".tab")
    .forEach((t) => t.classList.remove("active"));
  document.getElementById(tabId).classList.add("active");

  if (tabId === "vehicles") loadVehicles();
}

async function suggestVehicle(orderId) {
  try {
    const res = await fetch(`${API}/suggest_vehicle/${orderId}`);
    if (!res.ok) throw new Error("Не найдено");

    const vehicle = await res.json();
    alert(`Рекомендованная машина: ${vehicle.gos_number} (${vehicle.driver})`);
    document.getElementById("vehicleSelect").value = vehicle.id;
  } catch (e) {
    alert("Подходящая машина не найдена");
  }
}

function viewOrderDetails(orderId) {
  fetch(`${API}/orders/${orderId}`)
    .then((r) => r.json())
    .then((order) => {
      let cargosHtml = order.cargos
        .map(
          (c) =>
            `<li>${c.name} — ${c.weight}кг ×${c.quantity}, ${c.length}×${c.width}×${c.height}м, ${c.departure} → ${c.destination}</li>`,
        )
        .join("");
      let vehicle = order.vehicle
        ? `${order.vehicle.gos_number} (${order.vehicle.driver})`
        : "Не назначена";

      alert(`ЗАЯВКА #${order.id}
Статус: ${getStatusText(order.status)}
Машина: ${vehicle}
Грузы:
${cargosHtml}`);
    });
}

// ======================== АВТО-ОБНОВЛЕНИЕ ========================

async function exportToExcel() {
  const orders = await fetch(`${API}/orders`).then((r) => r.json());
  let csv = "ID,Создано,Статус,Машина,Грузов\n";
  orders.forEach((o) => {
    const vehicle = o.vehicle ? o.vehicle.gos_number : "-";
    csv += `${o.id},${new Date(o.created_at).toLocaleString()},${getStatusText(o.status)},${vehicle},${o.cargos.length}\n`;
  });
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "reyisy.csv";
  a.click();
}

loadOrders();
loadVehicles();
setInterval(() => {
  loadOrders();
  if (document.getElementById("vehicles").classList.contains("active"))
    loadVehicles();
}, 8000);
