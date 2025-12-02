// @ts-nocheck
const API = window.location.protocol + "//" + window.location.hostname + ":8080";

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
      <td>${order.cargos[0]?.departure || "-"} → ${order.cargos[order.cargos.length - 1]?.destination || "-"}</td>
      <td>${order.cargos.length}</td>
      <td>${getStatusText(order.status)}</td>
      <td>${vehicleInfo}</td>
      <td>${order.applicant || "-"}</td>
      <td>${order.department || "-"}</td>
      <td>${order.phone_number || "-"}</td>
      <td>${order.tent_type === "open" ? "Открытый" : "Закрытый"}</td>
      <td>
        ${order.status === "new" ? `<button class="btn" onclick="openAssignModal(${order.id})">Подобрать машину</button>` : ""}
        ${order.status === "assigned" ? `<button class="btn" onclick="completeOrder(${order.id})">Завершить рейс</button>` : ""}
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
      <td>${v.tent_type === "open" ? "Открытый" : "Закрытый"}</td>
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

let currentOrderId = null;

function openAssignModal(orderId) {
  currentOrderId = orderId;
  fetch(`${API}/orders/${orderId}`)
    .then((r) => r.json())
    .then((order) => {
      document.getElementById("modalOrderId").textContent = order.id;
      document.getElementById("modalCargoCount").textContent =
        order.cargos.length;
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

ymaps.ready(() => {
  const myMap = new ymaps.Map("map", { center: [53.9, 27.56], zoom: 10 });
  async function loadTracking() {
    const orders = await fetch(`${API}/orders`).then((r) => r.json());
    const active = orders.filter((o) => o.status === "assigned");
    active.forEach((o) => {
      const points = o.cargos.flatMap((c) => [c.departure, c.destination]);
      if (points.length) {
        ymaps.route(points).then((route) => myMap.geoObjects.add(route));
      }
    });
  }
  loadTracking();
});

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
        `ЗАЯВКА #${order.id}\nСоздано: ${new Date(order.created_at).toLocaleString("ru-RU")}\nСтатус: ${getStatusText(order.status)}\nМашина: ${vehicle}\nГрузы:\n${cargosHtml}`.trim(),
      );
    });
}

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

function showTab(tabId) {
  document
    .querySelectorAll(".tab")
    .forEach((t) => t.classList.remove("active"));
  document.getElementById(tabId).classList.add("active");
  if (tabId === "vehicles") loadVehicles();
}

function printTTN(orderId) {
  window.open(`${API}/ttn/${orderId}`);
}

async function exportToExcel() {
  window.location = `${API}/export_orders`;
}

loadOrders();
loadVehicles();
setInterval(() => {
  loadOrders();
  if (document.getElementById("vehicles").classList.contains("active"))
    loadVehicles();
}, 8000);
