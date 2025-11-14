const API_URL = "http://127.0.0.1:5000";

// Получаем данные из localStorage (ID выбранной машины и грузы)
let selectedVehicleId = null;
let cargos = [];

// Инициализация при загрузке страницы
document.addEventListener("DOMContentLoaded", function () {
  loadDataFromStorage();
  loadSelectedVehicle();
  loadAllVehicles();
});

function loadDataFromStorage() {
  // Получаем данные из localStorage
  const storedVehicleId = localStorage.getItem("selectedVehicleId");
  const storedCargos = localStorage.getItem("selectedCargos");

  if (storedVehicleId) {
    selectedVehicleId = parseInt(storedVehicleId);
  } else {
    showError(
      "Ошибка: данные о выбранной машине не найдены. Вернитесь на главную страницу.",
    );
    document.getElementById("confirmBtn").disabled = true;
  }

  if (storedCargos) {
    try {
      cargos = JSON.parse(storedCargos);
    } catch (e) {
      console.error("Error parsing cargos:", e);
    }
  }
}

async function loadSelectedVehicle() {
  if (!selectedVehicleId) return;

  try {
    const response = await fetch(`${API_URL}/vehicles`);
    if (!response.ok) throw new Error("Ошибка загрузки данных о машинах");

    const vehicles = await response.json();
    const vehicle = vehicles.find((v) => v.id === selectedVehicleId);

    if (vehicle) {
      displaySelectedVehicle(vehicle);
    } else {
      showError("Выбранная машина не найдена в базе данных");
    }
  } catch (error) {
    console.error("Error loading selected vehicle:", error);
    showError(`Ошибка загрузки данных: ${error.message}`);
  }
}

function displaySelectedVehicle(vehicle) {
  const detailsContainer = document.getElementById("vehicleDetails");

  // Вычисляем общий вес грузов
  const totalWeight = cargos.reduce(
    (sum, c) => sum + (c.weight || 0) * (c.quantity || 0),
    0,
  );

  detailsContainer.innerHTML = `
        <div class="vehicle-detail-item">
            <strong>Марка:</strong>
            <span>${vehicle.brand}</span>
        </div>
        <div class="vehicle-detail-item">
            <strong>Водитель:</strong>
            <span>${vehicle.driver}</span>
        </div>
        <div class="vehicle-detail-item">
            <strong>Гос. номер:</strong>
            <span>${vehicle.gos_number}</span>
        </div>
        <div class="vehicle-detail-item">
            <strong>Грузоподъёмность:</strong>
            <span>${vehicle.capacity} кг</span>
        </div>
        <div class="vehicle-detail-item">
            <strong>Длина кузова:</strong>
            <span>${vehicle.length} м</span>
        </div>
        <div class="vehicle-detail-item">
            <strong>Ширина кузова:</strong>
            <span>${vehicle.width} м</span>
        </div>
        <div class="vehicle-detail-item">
            <strong>Текущий статус:</strong>
            <span class="status-badge ${vehicle.status === "free" ? "status-free" : "status-busy"}">
                ${vehicle.status === "free" ? "Свободна" : "Занята"}
            </span>
        </div>
        <div class="vehicle-detail-item">
            <strong>Общий вес грузов:</strong>
            <span>${totalWeight.toFixed(2)} кг</span>
        </div>
        <div class="vehicle-detail-item">
            <strong>Количество грузов:</strong>
            <span>${cargos.length}</span>
        </div>
    `;
}

async function loadAllVehicles() {
  try {
    const response = await fetch(`${API_URL}/vehicles`);
    if (!response.ok) throw new Error("Ошибка загрузки списка машин");

    const vehicles = await response.json();
    displayAllVehicles(vehicles);
  } catch (error) {
    console.error("Error loading vehicles:", error);
    showError(`Ошибка загрузки списка машин: ${error.message}`);
  }
}

function displayAllVehicles(vehicles) {
  const tbody = document.getElementById("vehiclesTable").querySelector("tbody");
  tbody.innerHTML = "";

  vehicles.forEach((vehicle) => {
    const row = document.createElement("tr");
    // Подсвечиваем выбранную машину
    if (vehicle.id === selectedVehicleId) {
      row.style.backgroundColor = "#e8f5e9";
      row.style.fontWeight = "bold";
    }

    row.innerHTML = `
            <td>${vehicle.id}</td>
            <td>${vehicle.brand}</td>
            <td>${vehicle.driver}</td>
            <td>${vehicle.gos_number}</td>
            <td>${vehicle.capacity}</td>
            <td>${vehicle.length}</td>
            <td>${vehicle.width}</td>
            <td>
                <span class="status-badge ${vehicle.status === "free" ? "status-free" : "status-busy"}">
                    ${vehicle.status === "free" ? "Свободна" : "Занята"}
                </span>
            </td>
        `;
    tbody.appendChild(row);
  });
}

async function confirmSelection() {
  if (!selectedVehicleId) {
    showError("Ошибка: машина не выбрана");
    return;
  }

  const confirmBtn = document.getElementById("confirmBtn");
  confirmBtn.disabled = true;
  confirmBtn.textContent = "Обработка...";

  try {
    // Обновляем статус машины на "busy"
    const response = await fetch(`${API_URL}/vehicles/${selectedVehicleId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: "busy" }),
    });

    if (!response.ok) throw new Error("Ошибка обновления статуса машины");

    const updatedVehicle = await response.json();
    console.log("Vehicle status updated:", updatedVehicle);

    // Показываем сообщение об успехе
    showSuccess(
      `Успешно! Машина "${updatedVehicle.brand}" (${updatedVehicle.driver}) забронирована. Статус изменён на "Занята".`,
    );

    // Обновляем список машин
    await loadAllVehicles();
    await loadSelectedVehicle();

    // Очищаем localStorage
    localStorage.removeItem("selectedVehicleId");
    localStorage.removeItem("selectedCargos");

    // Меняем кнопку на "Вернуться на главную"
    confirmBtn.textContent = "Вернуться на главную";
    confirmBtn.onclick = function () {
      window.location.href = "index.html";
    };
    confirmBtn.disabled = false;
  } catch (error) {
    console.error("Error confirming selection:", error);
    showError(`Ошибка подтверждения: ${error.message}`);
    confirmBtn.disabled = false;
    confirmBtn.textContent = "Подтвердить выбор машины";
  }
}

function cancelSelection() {
  // Очищаем localStorage и возвращаемся на главную
  localStorage.removeItem("selectedVehicleId");
  localStorage.removeItem("selectedCargos");
  window.location.href = "index.html";
}

function showSuccess(message) {
  const successDiv = document.getElementById("successMessage");
  successDiv.textContent = message;
  successDiv.style.display = "block";

  const errorDiv = document.getElementById("errorMessage");
  errorDiv.style.display = "none";

  // Прокрутка к сообщению
  successDiv.scrollIntoView({ behavior: "smooth", block: "start" });
}

function showError(message) {
  const errorDiv = document.getElementById("errorMessage");
  errorDiv.textContent = message;
  errorDiv.style.display = "block";

  const successDiv = document.getElementById("successMessage");
  successDiv.style.display = "none";

  // Прокрутка к сообщению
  errorDiv.scrollIntoView({ behavior: "smooth", block: "start" });
}
