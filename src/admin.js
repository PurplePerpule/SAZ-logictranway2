// @ts-nocheck
const API = "";

let splitDialogOrderId = null;
let currentHistoryPage = 1;
let historyPageSize = 20;
let totalHistoryPages = 1;
let currentHistoryFilters = {};
let myMap = null;
let currentLocations = [];
let locationSearchTimeout = null;

function showLoader() {
  const loader = document.getElementById("loader");
  if (!loader) {
    // Создаем элемент загрузки если его нет
    const loaderDiv = document.createElement("div");
    loaderDiv.id = "loader";
    loaderDiv.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(255, 255, 255, 0.8);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 9999;
        `;
    loaderDiv.innerHTML = `
            <div style="text-align: center;">
                <div style="
                    width: 40px;
                    height: 40px;
                    border: 4px solid #f3f3f3;
                    border-top: 4px solid #3498db;
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                    margin: 0 auto;
                "></div>
                <p style="margin-top: 10px;">Загрузка...</p>
            </div>
        `;
    document.body.appendChild(loaderDiv);

    // Добавляем анимацию
    const style = document.createElement("style");
    style.innerHTML = `
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        `;
    document.head.appendChild(style);
  } else {
    loader.style.display = "flex";
  }
}

function hideLoader() {
  const loader = document.getElementById("loader");
  if (loader) {
    loader.style.display = "none";
  }
}

async function loadHistory() {
  try {
    document.body.style.cursor = "wait";

    // Проверяем авторизацию
    const token = localStorage.getItem("token");
    if (!token) {
      alert("Требуется авторизация");
      window.location.href = "login.html";
      return;
    }

    // Собираем фильтры
    const filters = {
      date_from: document.getElementById("filterDateFrom")?.value || "",
      date_to: document.getElementById("filterDateTo")?.value || "",
      vehicle_id: document.getElementById("filterVehicle")?.value || "",
      driver: document.getElementById("filterDriver")?.value || "",
      status: document.getElementById("filterStatus")?.value || "",
    };

    // Строим URL с параметрами
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value) params.append(key, value);
    });

    console.log("Загружаем историю рейсов с параметрами:", params.toString());

    const response = await fetch(`${API}/trips?${params.toString()}`, {
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(
        `Ошибка загрузки истории: ${response.status} - ${errorText}`,
      );
    }

    const trips = await response.json();
    console.log("Получено рейсов:", trips.length, trips);

    if (trips.length === 0) {
      alert("История рейсов пуста. Пока нет завершенных рейсов.");
    }

    renderHistoryTable(trips);
  } catch (error) {
    console.error("Ошибка загрузки истории:", error);
    alert(
      "Не удалось загрузить историю рейсов. Проверьте консоль для подробностей.",
    );
  } finally {
    document.body.style.cursor = "default";
  }
}

// Рендер таблицы истории
function renderHistoryTable(trips) {
  const tbody = document.querySelector("#historyTable tbody");
  if (!tbody) return;

  tbody.innerHTML = "";

  trips.forEach((trip) => {
    const tr = document.createElement("tr");
    tr.className = `trip-status-${trip.status}`;

    // Рассчитываем продолжительность
    let duration = "-";
    if (trip.started_at && trip.completed_at) {
      const start = new Date(trip.started_at);
      const end = new Date(trip.completed_at);
      const diffMs = end - start;
      const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
      const diffMinutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
      duration = `${diffHours}ч ${diffMinutes}м`;
    }

    // Информация о машине
    let vehicleInfo = "-";
    if (trip.vehicle) {
      vehicleInfo = `${trip.vehicle.brand} (${trip.vehicle.gos_number})`;
    }

    // Маршруты
    let routes = "-";
    if (trip.cargo_stats?.routes) {
      routes = trip.cargo_stats.routes.join("<br>");
    }

    // Статистика по грузам
    const cargoCount = trip.cargo_stats?.cargo_count || 0;
    const totalWeight = trip.cargo_stats?.total_weight || 0;
    const totalVolume = trip.cargo_stats?.total_volume || 0;

    // Статус с иконкой
    let statusBadge = "";
    switch (trip.status) {
      case "completed":
        statusBadge =
          '<span class="status-badge status-completed">✅ Завершен</span>';
        break;
      case "in_progress":
        statusBadge =
          '<span class="status-badge status-in-progress">🚚 В пути</span>';
        break;
      case "cancelled":
        statusBadge =
          '<span class="status-badge status-cancelled">❌ Отменен</span>';
        break;
      default:
        statusBadge = trip.status;
    }

    tr.innerHTML = `
            <td><strong>#${trip.id}</strong></td>
            <td>Заявка #${trip.order_id}</td>
            <td>${formatMSK(trip.started_at)}</td>
            <td>${trip.completed_at ? formatMSK(trip.completed_at) : "-"}</td>
            <td>${duration}</td>
            <td>${vehicleInfo}</td>
            <td>${trip.vehicle?.driver || "-"}</td>
            <td>${routes}</td>
            <td>${cargoCount} ед.</td>
            <td>${totalWeight.toFixed(1)} кг</td>
            <td>${totalVolume.toFixed(2)} м³</td>
            <td>${trip.order?.applicant || "-"}</td>
            <td>${statusBadge}</td>
            <td>
                <button class="btn" onclick="viewTripDetails(${trip.id})" title="Подробнее">
                    👁️
                </button>
                ${
                  trip.status === "in_progress"
                    ? `
                    <button class="btn" onclick="completeTrip(${trip.id})" title="Завершить рейс" style="background: #4caf50;">
                        ✓
                    </button>
                `
                    : ""
                }
            </td>
        `;

    tbody.appendChild(tr);
  });
}

async function unassignVehicle(orderId) {
  if (
    !confirm(
      "Снять машину с заявки? Машина будет освобождена, а заявка вернется в статус 'Новая'.",
    )
  )
    return;

  try {
    const token = localStorage.getItem("token");
    const response = await fetch(`${API}/orders/${orderId}/unassign`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
    });

    const result = await response.json();

    if (response.ok) {
      alert("Машина успешно снята с заявки");
      loadOrders();
      loadVehicles();
    } else {
      alert("Ошибка: " + result.error);
    }
  } catch (error) {
    console.error("Ошибка:", error);
    alert("Не удалось снять машину: " + error.message);
  }
}

// Просмотр деталей рейса
async function viewTripDetails(tripId) {
  try {
    const token = localStorage.getItem("token");
    if (!token) {
      alert("Требуется авторизация");
      window.location.href = "login.html";
      return;
    }

    console.log("Загружаем детали рейса #", tripId);

    const response = await fetch(`${API}/trips/${tripId}`, {
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      if (response.status === 404) {
        throw new Error("Рейс не найден");
      } else if (response.status === 403) {
        throw new Error("Доступ запрещен");
      } else {
        throw new Error(`Ошибка загрузки: ${response.status}`);
      }
    }

    const trip = await response.json();
    console.log("Данные рейса:", trip);

    // Формируем детальную информацию
    let details = `<h3>Рейс #${trip.id}</h3>`;
    details += `<p><strong>Статус:</strong> ${trip.status === "completed" ? "✅ Завершен" : "🚚 В пути"}</p>`;
    details += `<p><strong>Начало:</strong> ${formatMSK(trip.started_at)}</p>`;

    if (trip.completed_at) {
      details += `<p><strong>Завершение:</strong> ${formatMSK(trip.completed_at)}</p>`;
    }

    if (trip.distance_km) {
      details += `<p><strong>Пройдено км:</strong> ${trip.distance_km}</p>`;
    }

    if (trip.fuel_consumed) {
      details += `<p><strong>Потрачено топлива:</strong> ${trip.fuel_consumed} л</p>`;
    }

    if (trip.notes) {
      details += `<p><strong>Примечания:</strong> ${trip.notes}</p>`;
    }

    if (trip.order) {
      details += `<hr><h4>Информация о заявке</h4>`;
      details += `<p><strong>Заявка #${trip.order.id}</strong></p>`;
      details += `<p><strong>Заявитель:</strong> ${trip.order.applicant || "-"}</p>`;
      details += `<p><strong>Отдел:</strong> ${trip.order.department || "-"}</p>`;
      details += `<p><strong>Телефон:</strong> ${trip.order.phone_number || "-"}</p>`;

      if (trip.order.preferred_departure_time) {
        const time = new Date(trip.order.preferred_departure_time);
        details += `<p><strong>Желаемое время:</strong> ${time.toLocaleTimeString("ru-RU", { hour: "2-digit", minute: "2-digit" })}</p>`;
      }
    }

    // Проверяем, есть ли информация о машине в объекте рейса
    if (trip.vehicle) {
      details += `<hr><h4>Информация о транспорте</h4>`;
      details += `<p><strong>Машина:</strong> ${trip.vehicle.brand}</p>`;
      details += `<p><strong>Гос. номер:</strong> ${trip.vehicle.gos_number}</p>`;
      details += `<p><strong>Водитель:</strong> ${trip.vehicle.driver}</p>`;
      details += `<p><strong>Гаражный номер:</strong> ${trip.vehicle.garage_number}</p>`;
      details += `<p><strong>Тип тента:</strong> ${trip.vehicle.tent_type === "open" ? "Открытый" : "Закрытый"}</p>`;
    } else if (trip.vehicle_id) {
      // Если в объекте нет полной информации, но есть ID, загружаем отдельно
      try {
        const vehicleResponse = await fetch(
          `${API}/vehicles/${trip.vehicle_id}`,
        );
        if (vehicleResponse.ok) {
          const vehicle = await vehicleResponse.json();
          details += `<hr><h4>Информация о транспорте</h4>`;
          details += `<p><strong>Машина:</strong> ${vehicle.brand}</p>`;
          details += `<p><strong>Гос. номер:</strong> ${vehicle.gos_number}</p>`;
          details += `<p><strong>Водитель:</strong> ${vehicle.driver}</p>`;
          details += `<p><strong>Гаражный номер:</strong> ${vehicle.garage_number}</p>`;
          details += `<p><strong>Тип тента:</strong> ${vehicle.tent_type === "open" ? "Открытый" : "Закрытый"}</p>`;
        }
      } catch (e) {
        console.error("Не удалось загрузить данные машины:", e);
      }
    }

    if (trip.cargo_stats) {
      details += `<hr><h4>Грузы</h4>`;
      details += `<p><strong>Количество грузов:</strong> ${trip.cargo_stats.cargo_count}</p>`;
      details += `<p><strong>Общий вес:</strong> ${trip.cargo_stats.total_weight.toFixed(1)} кг</p>`;
      details += `<p><strong>Общий объем:</strong> ${trip.cargo_stats.total_volume.toFixed(2)} м³</p>`;

      if (trip.cargo_stats.routes && trip.cargo_stats.routes.length > 0) {
        details += `<p><strong>Маршруты:</strong></p><ul>`;
        trip.cargo_stats.routes.forEach((route) => {
          details += `<li>${route}</li>`;
        });
        details += `</ul>`;
      }
    }

    // Показываем в модальном окне
    if (typeof Swal !== "undefined") {
      Swal.fire({
        title: "Детали рейса",
        html: details,
        width: 700,
        showCloseButton: true,
        showConfirmButton: false,
      });
    } else {
      // Если Swal не загружен, показываем простой alert
      alert(details.replace(/<[^>]*>/g, ""));
    }
  } catch (error) {
    console.error("Ошибка:", error);
    alert("Не удалось загрузить детали рейса: " + error.message);
  }
}

// Завершение рейса
async function completeTrip(tripId) {
  if (!confirm("Завершить рейс и освободить машину?")) return;

  try {
    const token = localStorage.getItem("token");
    const response = await fetch(`${API}/trips/${tripId}/complete`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || "Ошибка завершения рейса");
    }

    alert("Рейс успешно завершен");
    loadHistory();
    loadVehicles();
  } catch (error) {
    console.error("Ошибка:", error);
    alert("Не удалось завершить рейс: " + error.message);
  }
}

// Применение фильтров
function applyHistoryFilters() {
  currentHistoryPage = 1;
  loadHistory();
}

// Сброс фильтров
function resetHistoryFilters() {
  document.getElementById("filterDateFrom").value = "";
  document.getElementById("filterDateTo").value = "";
  document.getElementById("filterVehicle").value = "";
  document.getElementById("filterDriver").value = "";
  document.getElementById("filterStatus").value = "";

  currentHistoryPage = 1;
  loadHistory();
}

// Пагинация
function changeHistoryPage(delta) {
  const newPage = currentHistoryPage + delta;
  if (newPage >= 1 && newPage <= totalHistoryPages) {
    currentHistoryPage = newPage;
    loadHistory();
  }
}

// Загрузка списка машин для фильтра
async function loadVehiclesForFilter() {
  try {
    const response = await fetch(`${API}/vehicles`);
    const vehicles = await response.json();

    const select = document.getElementById("filterVehicle");
    if (!select) return;

    select.innerHTML = '<option value="">Все машины</option>';
    vehicles.forEach((vehicle) => {
      const option = document.createElement("option");
      option.value = vehicle.id;
      option.textContent = `${vehicle.garage_number} - ${vehicle.brand} (${vehicle.driver})`;
      select.appendChild(option);
    });
  } catch (error) {
    console.error("Ошибка загрузки машин:", error);
  }
}

// Экспорт истории в Excel
async function exportHistoryToExcel() {
  try {
    // Собираем все фильтры для экспорта
    const params = new URLSearchParams(currentHistoryFilters);
    params.delete("page");
    params.delete("limit");

    window.open(`${API}/export_orders?${params.toString()}`);
  } catch (error) {
    console.error("Ошибка экспорта:", error);
    alert("Ошибка при экспорте истории");
  }
}

// Показать статистику рейсов
async function showTripStats() {
  const statsDiv = document.getElementById("tripStats");
  const statsContent = document.getElementById("statsContent");

  if (statsDiv.style.display === "block") {
    statsDiv.style.display = "none";
    return;
  }

  try {
    const response = await fetch(`${API}/trips/stats`);
    const stats = await response.json();

    let html = `
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px;">
                <div style="text-align: center; background: white; padding: 15px; border-radius: 8px;">
                    <h4 style="margin: 0; color: #2196f3;">Всего рейсов</h4>
                    <p style="font-size: 24px; font-weight: bold; margin: 10px 0;">${stats.total_trips}</p>
                </div>
                <div style="text-align: center; background: white; padding: 15px; border-radius: 8px;">
                    <h4 style="margin: 0; color: #4caf50;">Завершено</h4>
                    <p style="font-size: 24px; font-weight: bold; margin: 10px 0;">${stats.completed_trips}</p>
                </div>
                <div style="text-align: center; background: white; padding: 15px; border-radius: 8px;">
                    <h4 style="margin: 0; color: #ff9800;">В процессе</h4>
                    <p style="font-size: 24px; font-weight: bold; margin: 10px 0;">${stats.in_progress_trips}</p>
                </div>
                <div style="text-align: center; background: white; padding: 15px; border-radius: 8px;">
                    <h4 style="margin: 0; color: #9c27b0;">За 30 дней</h4>
                    <p style="font-size: 24px; font-weight: bold; margin: 10px 0;">${stats.recent_30_days.total}</p>
                </div>
            </div>
        `;

    // Топ машины
    if (stats.top_vehicles && stats.top_vehicles.length > 0) {
      html += `<h4 style="margin-top: 20px;">Самые активные машины:</h4>`;
      html += `<div style="overflow-x: auto;">`;
      html += `<table style="width: 100%; border-collapse: collapse;">`;
      html += `<tr><th>Машина</th><th>Водитель</th><th>Рейсов</th><th>Общий вес</th></tr>`;

      stats.top_vehicles.forEach((vehicle) => {
        html += `
                    <tr style="border-bottom: 1px solid #ddd;">
                        <td style="padding: 8px;">${vehicle.brand}</td>
                        <td style="padding: 8px;">${vehicle.driver}</td>
                        <td style="padding: 8px; text-align: center;">${vehicle.trip_count}</td>
                        <td style="padding: 8px; text-align: right;">${vehicle.total_weight.toFixed(0)} кг</td>
                    </tr>
                `;
      });

      html += `</table></div>`;
    }

    statsContent.innerHTML = html;
    statsDiv.style.display = "block";
  } catch (error) {
    console.error("Ошибка загрузки статистики:", error);
    statsContent.innerHTML =
      '<p style="color: red;">Не удалось загрузить статистику</p>';
    statsDiv.style.display = "block";
  }
}

// Функция принудительного вывода времени по Москве (UTC+3)
function formatMSK(dateString) {
  const date = new Date(dateString);
  const mskOffset = 6 * 60; // +3 часа в минутах
  const utc = date.getTime() + date.getTimezoneOffset() * 60000;
  const mskTime = new Date(utc + mskOffset * 60000);

  return mskTime.toLocaleString("ru-RU", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function renderOrdersTable(orders) {
  const tbody = document.querySelector("#ordersTable tbody");
  tbody.innerHTML = "";

  orders.forEach((order) => {
    const tr = document.createElement("tr");
    tr.className = `status-${order.status}`;

    // Добавляем класс приоритета
    if (order.priority === "high") tr.classList.add("priority-high");
    if (order.priority === "low") tr.classList.add("priority-low");

    // Форматируем дату создания
    let createdDate = "-";
    if (order.created_at) {
      const date = new Date(order.created_at);
      createdDate = date.toLocaleString("ru-RU", {
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    }

    // Форматируем желаемую дату отправления (используем preferred_departure_date)
    let preferredDate = "-";
    if (order.preferred_departure_date) {
      // order.preferred_departure_date приходит в формате "2024-12-15"
      // Преобразуем в русский формат даты
      const [year, month, day] = order.preferred_departure_date.split("-");
      preferredDate = `${day}.${month}.${year}`;
    }

    // Определяем маршрут
    let route = "-";
    if (order.cargos && order.cargos.length > 0) {
      const first = order.cargos[0];
      const last = order.cargos[order.cargos.length - 1];
      route = `${first.departure || "-"} → ${last.destination || "-"}`;
    }

    // Информация о машине
    let vehicleInfo = "-";
    if (order.vehicle) {
      vehicleInfo = `${order.vehicle.garage_number || ""} — ${order.vehicle.brand || ""} (${order.vehicle.driver || ""})`;
    }

    // Кнопки действий
    let actionButtons = "";

    if (order.status === "new") {
      actionButtons = `
        <button class="btn" onclick="openAssignModal(${order.id})">Подобрать машину</button>
        <button class="btn" onclick="openEditModal(${order.id})" style="background:#ff9800;">Изменить</button>
        <button class="btn" onclick="deleteOrder(${order.id})" style="background:#d32f2f;">Удалить</button>
        <button class="btn" onclick="viewOrderDetails(${order.id})">Подробно</button>
      `;
    } else if (order.status === "assigned") {
      actionButtons = `
        <button class="btn" onclick="completeOrder(${order.id})">Завершить рейс</button>
        <button class="btn" onclick="unassignVehicle(${order.id})" style="background:#ff9800;">Снять машину</button>
        <button class="btn" onclick="viewOrderDetails(${order.id})">Подробно</button>
        <button class="btn" onclick="printRouteSheet(${order.id})" style="background:#4caf50;">Маршрутный лист</button>
      `;
    } else if (order.status === "completed") {
      actionButtons = `
        <button class="btn" onclick="viewOrderDetails(${order.id})">Подробно</button>
        <button class="btn" onclick="printRouteSheet(${order.id})" style="background:#4caf50;">Маршрутный лист</button>
      `;
    } else {
      actionButtons = `<button class="btn" onclick="viewOrderDetails(${order.id})">Подробно</button>`;
    }

    tr.innerHTML = `
      <td><input type="checkbox" class="order-checkbox" value="${order.id}" onchange="updateSelection()"></td>
      <td>${order.id}</td>
      <td>${createdDate}</td>
      <td>${preferredDate}</td>
      <td>${route}</td>
      <td>${order.cargos ? order.cargos.length : 0}</td>
      <td>${getStatusText(order.status)}</td>
      <td>${vehicleInfo}</td>
      <td>${order.applicant || "-"}</td>
      <td>${order.department || "-"}</td>
      <td>${order.phone_number || "-"}</td>
      <td>${actionButtons}</td>
    `;

    tbody.appendChild(tr);
  });
}

let selectedOrders = [];

function toggleAllOrders(checkbox) {
  const checkboxes = document.querySelectorAll(".order-checkbox");
  checkboxes.forEach((cb) => (cb.checked = checkbox.checked));
  updateSelection();
}

function updateSelection() {
  const checkboxes = document.querySelectorAll(".order-checkbox:checked");
  selectedOrders = Array.from(checkboxes).map((cb) => parseInt(cb.value));
  document.getElementById("selectedCount").textContent =
    `${selectedOrders.length} выбрано`;
}

// Диалог объединения
function showMergeDialog() {
  if (selectedOrders.length < 2) {
    alert("Выберите минимум 2 заявки для объединения");
    return;
  }

  const list = document.getElementById("selectedOrdersList");
  list.innerHTML = selectedOrders
    .map((id) => `<div>Заявка #${id}</div>`)
    .join("");
  document.getElementById("mergeDialog").style.display = "block";
}

function closeMergeDialog() {
  document.getElementById("mergeDialog").style.display = "none";
}

async function confirmMerge() {
  try {
    const response = await fetch(`${API}/orders/merge`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${localStorage.getItem("token")}`,
      },
      body: JSON.stringify({ order_ids: selectedOrders }),
    });

    const result = await response.json();

    if (response.ok) {
      alert(`Заявки объединены в заявку #${result.new_order_id}`);
      closeMergeDialog();
      loadOrders();
    } else {
      alert("Ошибка: " + result.error);
    }
  } catch (error) {
    console.error("Ошибка объединения:", error);
    alert("Ошибка соединения с сервером");
  }
}

function updateStats(orders) {
  // Счетчики
  const pendingCount = orders.filter((o) => o.status === "new").length;
  const inTransitCount = orders.filter((o) => o.status === "assigned").length;

  // Завершено сегодня
  const today = new Date().toISOString().split("T")[0];
  const completedToday = orders.filter((o) => {
    if (o.status !== "completed") return false;
    if (!o.completed_at) return false;
    const completedDate = new Date(o.completed_at).toISOString().split("T")[0];
    return completedDate === today;
  }).length;

  // Обновляем DOM
  document.getElementById("pendingCount").textContent = pendingCount;
  document.getElementById("inTransitCount").textContent = inTransitCount;
  document.getElementById("completedToday").textContent = completedToday;
}

function sortOrders(column, type = "string") {
  let orders = window.currentOrders || [];

  orders.sort((a, b) => {
    let valA = a[column];
    let valB = b[column];

    if (type === "date") {
      valA = new Date(valA);
      valB = new Date(valB);
    }

    if (valA < valB) return -1;
    if (valA > valB) return 1;
    return 0;
  });

  renderOrdersTable(orders);
}

async function previewVehicleLoad(vehicleId, orderIds) {
  // Показать, как грузы будут размещены в машине
  try {
    const response = await fetch(`${API}/vehicles/${vehicleId}/load_preview`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${localStorage.getItem("token")}`,
      },
      body: JSON.stringify({ order_ids: orderIds }),
    });

    const result = await response.json();

    // Показать визуализацию загрузки
    showLoadPreview(result);
  } catch (error) {
    console.error("Ошибка предпросмотра:", error);
  }
}

async function splitOrder() {
  if (!splitDialogOrderId) return;

  try {
    // Для простоты разделяем на две равные части
    const orderRes = await fetch(`${API}/orders/${splitDialogOrderId}`);
    const order = await orderRes.json();

    if (order.cargos.length < 2) {
      alert("В заявке должен быть минимум 2 груза");
      return;
    }

    // Разделяем грузы пополам
    const mid = Math.ceil(order.cargos.length / 2);
    const firstHalf = order.cargos.slice(0, mid).map((c) => c.id);
    const secondHalf = order.cargos.slice(mid).map((c) => c.id);

    const response = await fetch(`${API}/orders/${splitDialogOrderId}/split`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${localStorage.getItem("token")}`,
      },
      body: JSON.stringify({
        split_groups: [firstHalf, secondHalf],
      }),
    });

    const result = await response.json();

    if (response.ok) {
      alert(`Заявка разделена на ${result.groups_count} части`);
      loadOrders();
    } else {
      alert("Ошибка: " + result.error);
    }
  } catch (error) {
    console.error("Ошибка разделения:", error);
    alert("Ошибка соединения с сервером");
  }
}

function showPriorityDialog() {
  if (selectedOrders.length === 0) {
    alert("Выберите заявки для изменения приоритета");
    return;
  }

  document.getElementById("priorityDialog").style.display = "block";
}

function closePriorityDialog() {
  document.getElementById("priorityDialog").style.display = "none";
}
// Диалог разделения
function showSplitDialog() {
  if (selectedOrders.length !== 1) {
    alert("Выберите одну заявку для разделения");
    return;
  }

  splitDialogOrderId = selectedOrders[0];
  // Здесь можно добавить более сложный интерфейс для распределения грузов
  if (confirm(`Разделить заявку #${splitDialogOrderId} на две равные части?`)) {
    splitOrder();
  }
}

async function loadOrders() {
  try {
    console.log("Загрузка заявок...");

    const res = await fetch(`${API}/orders`, {
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${localStorage.getItem("token")}`,
      },
    });

    if (!res.ok) {
      console.error("Ошибка HTTP:", res.status);
      throw new Error(`Ошибка HTTP: ${res.status}`);
    }

    const orders = await res.json();
    console.log("Получено заявок:", orders.length, "Первая заявка:", orders[0]);

    // Фильтрация
    const dateFilter = document.getElementById("dateFilter")?.value;
    const searchFilter =
      document.getElementById("searchFilter")?.value?.toLowerCase() || "";

    let filtered = orders;

    if (dateFilter) {
      filtered = filtered.filter((o) => {
        const orderDate = o.created_at?.split("T")[0];
        return orderDate === dateFilter;
      });
    }

    if (searchFilter) {
      filtered = filtered.filter((o) => {
        const driver = o.vehicle?.driver?.toLowerCase() || "";
        const gosNumber = o.vehicle?.gos_number?.toLowerCase() || "";
        const applicant = o.applicant?.toLowerCase() || "";
        return (
          driver.includes(searchFilter) ||
          gosNumber.includes(searchFilter) ||
          applicant.includes(searchFilter)
        );
      });
    }

    console.log("После фильтрации:", filtered.length);
    renderOrdersTable(filtered);
    updateStats(orders);
  } catch (err) {
    console.error("Ошибка загрузки заявок:", err);
    alert("Ошибка загрузки заявок: " + err.message);
  }
}

async function suggestVehicle(orderId) {
  try {
    const res = await fetch(`${API}/suggest_vehicle/${orderId}`);
    if (!res.ok) {
      const errorData = await res.json();
      throw new Error(errorData.error || "Не удалось подобрать машину");
    }
    const data = await res.json();

    // Проверяем, есть ли поле vehicle в ответе (новый формат)
    let vehicle;
    if (data.vehicle) {
      vehicle = data.vehicle;
      // Если есть предупреждение о разном типе тента
      if (data.warning) {
        alert(data.warning);
      }
    } else if (data.id) {
      // Старый формат: весь объект - это машина
      vehicle = data;
    } else {
      throw new Error("Не удалось получить данные о машине");
    }

    // Устанавливаем выбранную машину в селекте
    document.getElementById("vehicleSelect").value = vehicle.id;
    alert(`Рекомендована машина: ${vehicle.gos_number} (${vehicle.driver})`);
  } catch (error) {
    console.error("Error:", error);
    alert("Ошибка при подборе машины: " + error.message);
  }
}

// Умное распределение
async function autoDistributeSmart() {
  if (!confirm("Выполнить умное распределение всех нераспределенных заявок?")) {
    return;
  }

  try {
    const response = await fetch(`${API}/auto_distribute_smart`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${localStorage.getItem("token")}`,
      },
    });

    const result = await response.json();

    if (response.ok) {
      alert(
        `Умное распределение завершено!\n\nОбработано заявок: ${result.statistics.orders_processed}\nИспользовано машин: ${result.statistics.vehicles_used}`,
      );
      loadOrders();
      loadVehicles();
    } else {
      alert("Ошибка: " + result.error);
    }
  } catch (error) {
    console.error("Ошибка распределения:", error);
    alert("Ошибка соединения с сервером");
  }
}

async function loadVehicles() {
  try {
    const res = await fetch(`${API}/vehicles`, {
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${localStorage.getItem("token")}`,
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

  // Фильтруем заявки по статусу (показываем только новые и назначенные)
  const activeOrders = orders.filter((o) => o.status !== "completed");

  activeOrders.forEach((order) => {
    const tr = document.createElement("tr");
    tr.className = `status-${order.status}`;
    const vehicleInfo = order.vehicle
      ? `${order.vehicle.garage_number} — ${order.vehicle.brand} (${order.vehicle.driver})`
      : "—";

    // Форматируем время отправления
    let preferredTime = "-";
    if (order.preferred_departure_time) {
      const time = new Date(order.preferred_departure_time);
      preferredTime = time.toLocaleTimeString("ru-RU", {
        hour: "2-digit",
        minute: "2-digit",
      });
    }

    // Определяем маршрут
    let route = "-";
    if (order.cargos && order.cargos.length > 0) {
      const first = order.cargos[0];
      const last = order.cargos[order.cargos.length - 1];
      route = `${first.departure} → ${last.destination}`;
    }

    // Определяем типы тента грузов
    let tentTypes = "-";
    if (order.cargos && order.cargos.length > 0) {
      const types = [
        ...new Set(order.cargos.map((c) => c.tent_type || "closed")),
      ];
      tentTypes = types
        .map((t) => (t === "open" ? "Открытый" : "Закрытый"))
        .join(", ");
    }

    tr.innerHTML = `
      <td>${order.id}</td>
      <td>${formatMSK(order.created_at)}</td>
      <td>${preferredTime}</td>
      <td>${route}</td>
      <td>${order.cargos ? order.cargos.length : 0}</td>
      <td>${getStatusText(order.status)}</td>
      <td>${vehicleInfo}</td>
      <td>${order.applicant || "-"}</td>
      <td>${order.department || "-"}</td>
      <td>${order.phone_number || "-"}</td>
      <td>
        ${
          order.status === "new"
            ? `
          <button class="btn" onclick="openAssignModal(${order.id})">Подобрать машину</button>
          <button class="btn" onclick="openEditModal(${order.id})" style="background:#ff9800;">Изменить</button>
          <button class="btn" onclick="deleteOrder(${order.id})" style="background:#d32f2f;">Удалить</button>
        `
            : ""
        }
        ${
          order.status === "assigned"
            ? `<button class="btn" onclick="completeOrder(${order.id})">Завершить</button>
        <button class="btn" onclick="unassignVehicle(${order.id})" style="background:#ff9800;">Снять машину</button>`
            : ""
        }
        <button class="btn" onclick="viewOrderDetails(${order.id})">Подробно</button>
        ${
          order.status === "assigned" || order.status === "completed"
            ? `

            <button class="btn" onclick="printRouteSheet(${order.id})" style="background:#4caf50;">Маршрутный лист</button>
        `
            : ""
        }
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
      <td><span class="status-badge ${v.status === "free" ? "status-free" : v.status === "in_repair" ? "status-repair" : "status-busy"}">
        ${v.status === "free" ? "Свободна" : v.status === "in_repair" ? "В ремонте" : "Занята"}
      </span></td>
    `;
    tbody.appendChild(tr);
  });

  // Заполняем селекты
  ["vehicleStatusSelect", "trackingVehicleSelect"].forEach((id) => {
    const sel = document.getElementById(id);
    if (!sel) return;
    const selected = sel.value;
    sel.innerHTML = '<option value="">— Выберите машину —</option>';
    vehicles.forEach((v) => {
      const opt = document.createElement("option");
      opt.value = v.id;
      opt.textContent = `${v.garage_number} — ${v.brand} (${v.driver})`;
      sel.appendChild(opt);
    });
    if (selected) sel.value = selected;
  });
}

function applyVehicleStatus() {
  const vehicleSel = document.getElementById("vehicleStatusSelect");
  const statusSel = document.getElementById("vehicleNewStatus");
  if (!vehicleSel?.value || !statusSel?.value)
    return alert("Выберите машину и статус");

  fetch(`${API}/vehicles/${vehicleSel.value}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${localStorage.getItem("token")}`,
    },
    body: JSON.stringify({ status: statusSel.value }),
  })
    .then(async (res) => {
      if (!res.ok) throw new Error((await res.json()).error || "Ошибка");
      alert("Статус обновлён");
      loadVehicles();
    })
    .catch((e) => alert(e.message || "Ошибка"));
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
      <td>${formatMSK(order.created_at)}</td>
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
          // Показываем все машины, но выделяем свободные
          const select = document.getElementById("vehicleSelect");
          select.innerHTML = '<option value="">— Выберите машину —</option>';

          // Сначала добавляем свободные машины
          const freeVehicles = vehicles.filter((v) => v.status === "free");
          freeVehicles.forEach((v) => {
            const opt = document.createElement("option");
            opt.value = v.id;
            opt.textContent = `${v.garage_number} — ${v.brand} (${v.driver}) — ${v.capacity} кг [Свободна]`;
            select.appendChild(opt);
          });

          // Затем добавляем разделитель
          const separator = document.createElement("option");
          separator.disabled = true;
          separator.textContent = "──────────";
          select.appendChild(separator);

          // Затем добавляем занятые машины
          const busyVehicles = vehicles.filter(
            (v) => v.status !== "free" && v.status !== "in_repair",
          );
          busyVehicles.forEach((v) => {
            const opt = document.createElement("option");
            opt.value = v.id;
            opt.disabled = true;
            opt.textContent = `${v.garage_number} — ${v.brand} (${v.driver}) — ${v.capacity} кг [Занята]`;
            select.appendChild(opt);
          });

          // Затем добавляем машины в ремонте
          const repairVehicles = vehicles.filter(
            (v) => v.status === "in_repair",
          );
          repairVehicles.forEach((v) => {
            const opt = document.createElement("option");
            opt.value = v.id;
            opt.disabled = true;
            opt.textContent = `${v.garage_number} — ${v.brand} (${v.driver}) — ${v.capacity} кг [В ремонте]`;
            select.appendChild(opt);
          });

          // Автоматически подбираем машину при открытии модального окна
          suggestVehicle(orderId);
        });
    });
  document.getElementById("assignModal").style.display = "block";
}

// Функции для работы с пользователями
function openAddUserModal() {
  document.getElementById("addUserModal").style.display = "block";
}

function closeAddUserModal() {
  document.getElementById("addUserModal").style.display = "none";
  document.getElementById("newUsername").value = "";
  document.getElementById("newPassword").value = "";
  document.getElementById("newFullName").value = "";
  document.getElementById("newDepartment").value = "";
  document.getElementById("newPhone").value = "";
  document.getElementById("newRole").value = "user";
}

async function loadUsers() {
  try {
    const res = await fetch(`${API}/users`, {
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${localStorage.getItem("token")}`,
      },
    });
    const users = await res.json();
    renderUsers(users);
  } catch (err) {
    console.error("Ошибка загрузки пользователей:", err);
  }
}

function renderUsers(users) {
  const tbody = document.querySelector("#usersTable tbody");
  if (!tbody) return;

  tbody.innerHTML = "";
  users.forEach((user) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
            <td>${user.id}</td>
            <td>${user.username}</td>
            <td>${user.full_name || "-"}</td>
            <td>${user.department || "-"}</td>
            <td>${user.phone_number || "-"}</td>
            <td>${user.role === "admin" ? "Администратор" : "Пользователь"}</td>
            <td>
                <button class="btn" onclick="editUser(${user.id})">Изменить</button>
                ${
                  user.id !== currentUserId
                    ? `<button class="btn" style="background:#d32f2f" onclick="deleteUser(${user.id})">Удалить</button>`
                    : ""
                }
            </td>
        `;
    tbody.appendChild(tr);
  });
}

async function addUser() {
  const username = document.getElementById("newUsername").value.trim();
  const password = document.getElementById("newPassword").value;
  const fullName = document.getElementById("newFullName").value.trim();
  const department = document.getElementById("newDepartment").value.trim();
  const phone = document.getElementById("newPhone").value.trim();
  const role = document.getElementById("newRole").value;

  if (!username || !password) {
    alert("Логин и пароль обязательны");
    return;
  }

  try {
    const res = await fetch(`${API}/register`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${localStorage.getItem("token")}`,
      },
      body: JSON.stringify({
        username,
        password,
        full_name: fullName || null,
        department: department || null,
        phone_number: phone || null,
        role,
      }),
    });

    if (res.ok) {
      alert("Пользователь создан");
      closeAddUserModal();
      loadUsers();
    } else {
      const error = await res.json();
      alert(error.error || "Ошибка создания пользователя");
    }
  } catch (err) {
    console.error("Ошибка создания пользователя:", err);
    alert("Ошибка соединения с сервером");
  }
}

async function deleteUser(userId) {
  if (!confirm("Удалить пользователя?")) return;

  try {
    const res = await fetch(`${API}/users/${userId}`, {
      method: "DELETE",
      headers: {
        Authorization: `Bearer ${localStorage.getItem("token")}`,
      },
    });

    if (res.ok) {
      alert("Пользователь удалён");
      loadUsers();
    } else {
      const error = await res.json();
      alert(error.error || "Ошибка удаления пользователя");
    }
  } catch (err) {
    console.error("Ошибка удаления пользователя:", err);
    alert("Ошибка соединения с сервером");
  }
}

async function editUser(userId) {
  const newPassword = prompt(
    "Введите новый пароль (оставьте пустым, чтобы не менять):",
  );
  const newFullName = prompt("Введите ФИО:", "");
  const newDepartment = prompt("Введите отдел:", "");
  const newPhone = prompt("Введите телефон:", "");

  const updates = {};
  if (newPassword) updates.password = newPassword;
  if (newFullName !== null) updates.full_name = newFullName;
  if (newDepartment !== null) updates.department = newDepartment;
  if (newPhone !== null) updates.phone_number = newPhone;

  if (Object.keys(updates).length === 0) return;

  try {
    const res = await fetch(`${API}/users/${userId}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${localStorage.getItem("token")}`,
      },
      body: JSON.stringify(updates),
    });

    if (res.ok) {
      alert("Данные пользователя обновлены");
      loadUsers();
    } else {
      const error = await res.json();
      alert(error.error || "Ошибка обновления пользователя");
    }
  } catch (err) {
    console.error("Ошибка обновления пользователя:", err);
    alert("Ошибка соединения с сервером");
  }
}

// Обновляем главную функцию для хранения ID текущего пользователя
let currentUserId = null;

async function loadCurrentUser() {
  try {
    const res = await fetch(`${API}/me`, {
      headers: {
        Authorization: `Bearer ${localStorage.getItem("token")}`,
      },
    });
    if (res.ok) {
      const user = await res.json();
      currentUserId = user.id;
    }
  } catch (err) {
    console.error("Ошибка загрузки данных пользователя:", err);
  }
}

// Вызываем при загрузке

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
      body: JSON.stringify({ vehicle_id: +vehicleId }),
    });

    if (res.ok) {
      alert("Машина успешно назначена!");
      closeAssignModal();
      loadOrders();
      loadVehicles();
    } else {
      const err = await res.json();
      alert("Ошибка: " + (err.error || "Неизвестная ошибка"));
    }
  } catch (e) {
    console.error("Ошибка назначения машины:", e);
    alert("Ошибка связи с сервером");
  }
}

ymaps.ready(() => {
  myMap = new ymaps.Map("map", { center: [53.9, 27.56], zoom: 10 });

  window.trackingShowRoute = async function () {
    if (!myMap) return;
    myMap.geoObjects.removeAll();
    const sel = document.getElementById("trackingVehicleSelect");
    if (!sel?.value) return alert("Выберите машину");

    const vehicleId = +sel.value;
    const orders = await fetch(`${API}/orders`).then((r) => r.json());
    const active = orders.filter(
      (o) => o.status === "assigned" && o.vehicle?.id === vehicleId,
    );

    if (!active.length)
      return alert("Для выбранной машины нет активного рейса");

    for (const o of active) {
      const points = o.cargos.flatMap((c) => [c.departure, c.destination]);
      if (points.length)
        await ymaps.route(points).then((route) => myMap.geoObjects.add(route));
    }
  };

  window.trackingClear = () => myMap?.geoObjects.removeAll();
});

async function completeOrder(orderId) {
  if (!confirm("Завершить рейс и освободить машину?")) return;
  const res = await fetch(`${API}/orders/${orderId}/complete`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${localStorage.getItem("token")}`,
    },
  });
  if (res.ok) {
    alert("Рейс завершён, машина освобождена");
    loadOrders();
    loadVehicles();
  } else alert("Ошибка");
}

function viewOrderDetails(orderId) {
  fetch(`${API}/orders/${orderId}`)
    .then((r) => r.json())
    .then((order) => {
      let cargosHtml = "";
      order.cargos.forEach((c) => {
        const tentType = c.tent_type === "open" ? "Открытый" : "Закрытый";
        cargosHtml += `<li>${c.name} — ${c.weight}кг ×${c.quantity}, ${c.length}×${c.width}×${c.height}м (${tentType}), ${c.departure} → ${c.destination}</li>`;
      });
      const vehicle = order.vehicle
        ? `${order.vehicle.garage_number} — ${order.vehicle.brand} (${order.vehicle.driver})`
        : "Не назначена";

      // Форматируем время
      let preferredTime = "Не указано";
      if (order.preferred_departure_time) {
        const time = new Date(order.preferred_departure_time);
        preferredTime = time.toLocaleTimeString("ru-RU", {
          hour: "2-digit",
          minute: "2-digit",
        });
      }

      alert(
        `ЗАЯВКА #${order.id}\n` +
          `Создано: ${formatMSK(order.created_at)}\n` +
          `Желаемое время отправления: ${preferredTime}\n` +
          `Статус: ${getStatusText(order.status)}\n` +
          `Машина: ${vehicle}\n` +
          `Заявитель: ${order.applicant || "-"}\n` +
          `Отдел: ${order.department || "-"}\n` +
          `Телефон: ${order.phone_number || "-"}\n` +
          `Грузы:\n${cargosHtml}`,
      );
    });
}

function getStatusText(status) {
  const statusMap = {
    new: "Новая",
    assigned: "Назначена",
    completed: "Завершена",
    in_progress: "В пути",
  };
  return statusMap[status] || status;
}

async function openEditModal(orderId) {
  try {
    const res = await fetch(`${API}/orders/${orderId}`, {
      headers: {
        Authorization: `Bearer ${localStorage.getItem("token")}`,
      },
    });

    if (!res.ok) {
      throw new Error("Не удалось загрузить заявку");
    }

    const order = await res.json();
    currentOrderId = orderId;

    // Заполняем поля формы
    document.getElementById("editOrderId").textContent = order.id;
    document.getElementById("editApplicant").value = order.applicant || "";
    document.getElementById("editDepartment").value = order.department || "";
    document.getElementById("editCompany").value = order.company_name || "";
    document.getElementById("editPhone").value = order.phone_number || "";
    document.getElementById("editNote").value = order.note || "";

    // ЗАМЕНА: Заполняем ДАТУ вместо времени
    if (order.preferred_departure_date) {
      // order.preferred_departure_date приходит в формате "2024-12-15"
      document.getElementById("editPreferredDate").value =
        order.preferred_departure_date;
    } else {
      document.getElementById("editPreferredDate").value = "";
    }

    document.getElementById("editOrderModal").style.display = "block";
  } catch (error) {
    console.error("Ошибка открытия модального окна:", error);
    alert("Не удалось загрузить данные заявки");
  }
}

function closeEditModal() {
  document.getElementById("editOrderModal").style.display = "none";
}

async function savePriority() {
  const priority = document.getElementById("prioritySelect").value;

  try {
    // Обновляем приоритет для каждой выбранной заявки
    for (const orderId of selectedOrders) {
      await fetch(`${API}/orders/${orderId}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
        body: JSON.stringify({ priority: priority }),
      });
    }

    alert("Приоритеты обновлены");
    closePriorityDialog();
    loadOrders();
  } catch (error) {
    console.error("Ошибка обновления приоритета:", error);
    alert("Ошибка соединения с сервером");
  }
}

async function saveOrderChanges() {
  const data = {
    company_name: document.getElementById("editCompany").value, // НОВОЕ
    applicant: document.getElementById("editApplicant").value,
    department: document.getElementById("editDepartment").value,
    phone_number: document.getElementById("editPhone").value,
    tent_type: document.getElementById("editTentType").value,
    preferred_departure_date:
      document.getElementById("editPreferredDate").value || null,
    note: document.getElementById("editNote").value,
  };

  const res = await fetch(`${API}/orders/${currentOrderId}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${localStorage.getItem("token")}`,
    },
    body: JSON.stringify(data),
  });

  if (res.ok) {
    alert("Заявка обновлена");
    closeEditModal();
    loadOrders();
  } else {
    const err = await res.json();
    alert("Ошибка: " + (err.error || "неизвестно"));
  }
}

async function deleteOrder(orderId) {
  if (
    !confirm("Удалить заявку №" + orderId + "? Это действие нельзя отменить!")
  )
    return;
  const res = await fetch(`${API}/orders/${orderId}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
  });
  if (res.ok) {
    alert("Заявка удалена");
    loadOrders();
  } else {
    const err = await res.json();
    alert("Ошибка: " + (err.error || "нельзя удалить"));
  }
}

async function mergeOrders() {
  const selectedOrders = Array.from(
    document.querySelectorAll(".order-checkbox:checked"),
  ).map((cb) => parseInt(cb.value));

  if (selectedOrders.length < 2) {
    alert("Выберите минимум 2 заявки для объединения");
    return;
  }

  if (
    !confirm(`Объединить ${selectedOrders.length} выбранных заявок в одну?`)
  ) {
    return;
  }

  try {
    const response = await fetch(`${API}/orders/merge`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${localStorage.getItem("token")}`,
      },
      body: JSON.stringify({ order_ids: selectedOrders }),
    });

    const result = await response.json();

    if (response.ok) {
      alert(`Заявки объединены в заявку #${result.new_order_id}`);
      loadOrders();
    } else {
      alert("Ошибка: " + result.error);
    }
  } catch (error) {
    console.error("Ошибка объединения:", error);
    alert("Ошибка соединения с сервером");
  }
}

function showTab(tabId) {
  console.log("Переключение на вкладку:", tabId);

  // Скрываем все вкладки
  document.querySelectorAll(".tab").forEach((t) => {
    t.classList.remove("active");
  });

  // Показываем выбранную вкладку
  const targetTab = document.getElementById(tabId);
  if (targetTab) {
    targetTab.classList.add("active");
  } else {
    console.error("Вкладка не найдена:", tabId);
    return;
  }

  // Показывать/скрывать чекбоксы только во вкладке заявок
  const selectionMode = document.getElementById("selectionMode");
  if (selectionMode) {
    if (tabId === "orders") {
      selectionMode.style.display = "block";
    } else {
      selectionMode.style.display = "none";
      // Сбрасываем выделение при переключении вкладок
      selectedOrders = [];
      updateSelection();
    }
  }

  // Загружаем данные для выбранной вкладки
  switch (tabId) {
    case "orders":
      loadOrders();
      break;
    case "vehicles":
      loadVehicles();
      break;
    case "history":
      loadHistory();
      loadVehiclesForFilter();
      break;
    case "tracking":
      // Инициализируем карту если нужно
      if (typeof ymaps !== "undefined" && !myMap) {
        ymaps.ready(() => {
          myMap = new ymaps.Map("map", { center: [53.9, 27.56], zoom: 10 });
        });
      }
      break;
    case "users":
      loadUsers();
      break;
    case "locations":
      showLocationsTab();
      break;
  }
}

function printRouteSheet(orderId) {
  window.open(
    `${API}/route_sheet/${orderId}`,
    "_blank",
    "width=1200,height=800",
  );
}
async function exportToExcel() {
  window.location = `${API}/export_orders`;
}

document.addEventListener("DOMContentLoaded", function () {
  console.log("Админ-панель загружена");

  // Проверка авторизации
  const token = localStorage.getItem("token");
  if (!token) {
    window.location.href = "login.html";
    return;
  }

  // Проверяем валидность токена
  fetch(`${API}/me`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error("Invalid token");
      }
      return response.json();
    })
    .then((user) => {
      console.log("Авторизован как:", user.username);
      currentUserId = user.id;
    })
    .catch((error) => {
      console.error("Ошибка авторизации:", error);
      localStorage.removeItem("token");
      window.location.href = "login.html";
      return;
    });

  // Инициализация переменных
  window.API = API || "";
  currentHistoryPage = 1;

  // Загружаем данные для вкладки по умолчанию
  if (document.getElementById("orders")?.classList.contains("active")) {
    loadOrders();
  }

  // Загружаем транспорт
  loadVehicles();

  // Инициализируем вкладки
  initTabs();

  // Автообновление каждые 10 секунд
  setInterval(() => {
    if (document.getElementById("orders")?.classList.contains("active")) {
      loadOrders();
    }
    if (document.getElementById("vehicles")?.classList.contains("active")) {
      loadVehicles();
    }
  }, 10000);
});

// Показать вкладку адресов
function showLocationsTab() {
  loadLocations();
}

// Загрузка адресов
async function loadLocations() {
  try {
    const search = document.getElementById("locationSearch")?.value || "";
    const type = document.getElementById("locationTypeFilter")?.value || "";

    let url = `${API}/locations?search=${encodeURIComponent(search)}`;
    if (type === "departure") url += "&departure_only=true";
    if (type === "destination") url += "&destination_only=true";

    const response = await fetch(url, {
      headers: {
        Authorization: `Bearer ${localStorage.getItem("token")}`,
      },
    });

    currentLocations = await response.json();
    renderLocationsTable(currentLocations);
  } catch (error) {
    console.error("Ошибка загрузки адресов:", error);
    alert("Не удалось загрузить адреса");
  }
}

// Поиск с задержкой
function searchLocations() {
  if (locationSearchTimeout) {
    clearTimeout(locationSearchTimeout);
  }
  locationSearchTimeout = setTimeout(loadLocations, 500);
}

function resetLocationSearch() {
  document.getElementById("locationSearch").value = "";
  document.getElementById("locationTypeFilter").value = "";
  loadLocations();
}

// Рендер таблицы адресов
function renderLocationsTable(locations) {
  const tbody = document.querySelector("#locationsTable tbody");
  if (!tbody) return;

  tbody.innerHTML = "";

  locations.forEach((location) => {
    const tr = document.createElement("tr");

    // Определяем типы
    let types = [];
    if (location.is_departure) types.push("Отправление");
    if (location.is_destination) types.push("Назначение");

    tr.innerHTML = `
            <td>${location.id}</td>
            <td>${location.company_name || "-"}</td>
            <td>${location.address}</td>
            <td>${types.join(", ")}</td>
            <td>${location.contact_person || "-"}</td>
            <td>${location.phone_number || "-"}</td>
            <td>
                <button class="btn" onclick="editLocation(${location.id})">Изменить</button>
                <button class="btn" style="background:#d32f2f" onclick="deleteLocation(${location.id})">Удалить</button>
            </td>
        `;
    tbody.appendChild(tr);
  });
}

// Открыть модальное окно добавления
function openAddLocationModal() {
  document.getElementById("locationModalTitle").textContent = "Добавить адрес";
  document.getElementById("editLocationId").value = "";
  document.getElementById("locationCompany").value = "";
  document.getElementById("locationAddress").value = "";
  document.getElementById("locationIsDeparture").checked = true;
  document.getElementById("locationIsDestination").checked = true;
  document.getElementById("locationContact").value = "";
  document.getElementById("locationPhone").value = "";
  document.getElementById("locationEmail").value = "";
  document.getElementById("locationNotes").value = "";
  document.getElementById("saveLocationBtn").textContent = "Сохранить";

  document.getElementById("locationModal").style.display = "block";
}

// Закрыть модальное окно
function closeLocationModal() {
  document.getElementById("locationModal").style.display = "none";
}

// Сохранить адрес
async function saveLocation() {
  const id = document.getElementById("editLocationId").value;
  const isEdit = !!id;

  const data = {
    company_name: document.getElementById("locationCompany").value.trim(),
    address: document.getElementById("locationAddress").value.trim(),
    is_departure: document.getElementById("locationIsDeparture").checked,
    is_destination: document.getElementById("locationIsDestination").checked,
    contact_person:
      document.getElementById("locationContact").value.trim() || null,
    phone_number: document.getElementById("locationPhone").value.trim() || null,
    email: document.getElementById("locationEmail").value.trim() || null,
    notes: document.getElementById("locationNotes").value.trim() || null,
  };

  if (!data.address) {
    alert("Адрес обязателен для заполнения");
    return;
  }

  try {
    const url = isEdit ? `${API}/locations/${id}` : `${API}/locations`;
    const method = isEdit ? "PUT" : "POST";

    const response = await fetch(url, {
      method: method,
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${localStorage.getItem("token")}`,
      },
      body: JSON.stringify(data),
    });

    if (response.ok) {
      alert(`Адрес ${isEdit ? "обновлен" : "добавлен"}`);
      closeLocationModal();
      loadLocations();
    } else {
      const error = await response.json();
      alert(error.error || "Ошибка сохранения");
    }
  } catch (error) {
    console.error("Ошибка сохранения адреса:", error);
    alert("Ошибка соединения с сервером");
  }
}

// Редактировать адрес
async function editLocation(id) {
  const location = currentLocations.find((loc) => loc.id === id);
  if (!location) return;

  document.getElementById("locationModalTitle").textContent =
    "Редактировать адрес";
  document.getElementById("editLocationId").value = location.id;
  document.getElementById("locationCompany").value =
    location.company_name || "";
  document.getElementById("locationAddress").value = location.address;
  document.getElementById("locationIsDeparture").checked =
    location.is_departure;
  document.getElementById("locationIsDestination").checked =
    location.is_destination;
  document.getElementById("locationContact").value =
    location.contact_person || "";
  document.getElementById("locationPhone").value = location.phone_number || "";
  document.getElementById("locationEmail").value = location.email || "";
  document.getElementById("locationNotes").value = location.notes || "";
  document.getElementById("saveLocationBtn").textContent = "Обновить";

  document.getElementById("locationModal").style.display = "block";
}

// Удалить адрес
async function deleteLocation(id) {
  if (!confirm("Удалить этот адрес?")) return;

  try {
    const response = await fetch(`${API}/locations/${id}`, {
      method: "DELETE",
      headers: {
        Authorization: `Bearer ${localStorage.getItem("token")}`,
      },
    });

    if (response.ok) {
      alert("Адрес удален");
      loadLocations();
    } else {
      const error = await response.json();
      alert(error.error || "Ошибка удаления");
    }
  } catch (error) {
    console.error("Ошибка удаления адреса:", error);
    alert("Ошибка соединения с сервером");
  }
}

// Импорт из файла
function openBulkImportModal() {
  document.getElementById("importFile").value = "";
  document.getElementById("importModal").style.display = "block";
}

function closeImportModal() {
  document.getElementById("importModal").style.display = "none";
}

async function uploadImportFile() {
  const fileInput = document.getElementById("importFile");
  if (!fileInput.files.length) {
    alert("Выберите файл");
    return;
  }

  const formData = new FormData();
  formData.append("file", fileInput.files[0]);

  try {
    const response = await fetch(`${API}/locations/bulk_import`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${localStorage.getItem("token")}`,
      },
      body: formData,
    });

    const result = await response.json();

    if (response.ok) {
      alert(
        `Импорт завершен. Добавлено: ${result.imported}, Пропущено: ${result.skipped}`,
      );
      closeImportModal();
      loadLocations();
    } else {
      alert(result.error || "Ошибка импорта");
    }
  } catch (error) {
    console.error("Ошибка импорта:", error);
    alert("Ошибка соединения с сервером");
  }
}

// Экспорт в Excel
async function exportLocations() {
  window.open(`${API}/export_locations`, "_blank");
}

async function logout() {
  try {
    const token = localStorage.getItem("token");
    if (token) {
      await fetch("/logout", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
      });
    }
  } catch (error) {
    console.error("Ошибка при выходе:", error);
  } finally {
    // Очищаем localStorage
    localStorage.removeItem("token");
    localStorage.removeItem("userRole");
    localStorage.removeItem("userId");
    localStorage.removeItem("username");

    // Перенаправляем на страницу входа
    window.location.href = "/login.html";
  }
}

function initTabs() {
  // Добавляем обработчики для всех вкладок через делегирование событий
  const nav = document.querySelector("nav");
  if (nav) {
    nav.addEventListener("click", function (e) {
      e.preventDefault();
      const target = e.target;
      if (target.tagName === "A") {
        const tabId = target
          .getAttribute("onclick")
          ?.match(/['"]([^'"]+)['"]/)?.[1];
        if (tabId) {
          showTab(tabId);
        }
      }
    });
  }

  // Инициализируем активную вкладку
  const activeTab = document.querySelector(".tab.active");
  if (activeTab) {
    const tabId = activeTab.id;
    showTab(tabId);
  }
}
