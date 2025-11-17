ymaps.ready(init);

var myMap;

function init() {
  myMap = new ymaps.Map("map", {
    center: [54.54, 26.38], // Координаты центра карты (Москва по умолчанию)
    zoom: 10,
  });
  loadCargos();
}

const API_URL = "http://127.0.0.1:5000";

async function loadCargos() {
  try {
    const response = await fetch(API_URL + "/cargos");
    const data = await response.json();
    updateCargoList(data);
    return data;
  } catch (error) {
    alert(`Ошибка при загрузке грузов: ${error.message}`);
    return [];
  }
}

// Функция для построения маршрута
async function buildRoute() {
  const cargos = await loadCargos(); // Get fresh data from API

  if (cargos.length === 0) {
    // Если список пуст, очищаем карту
    myMap.geoObjects.removeAll();
    return;
  }

  // Очистка предыдущих объектов на карте
  myMap.geoObjects.removeAll();

  // Собираем все уникальные точки для построения оптимального маршрута
  const allPoints = [];
  const pointsMap = new Map(); // Для отслеживания уникальных точек

  for (const cargo of cargos) {
    // Добавляем точку отправления
    if (!pointsMap.has(cargo.departure)) {
      pointsMap.set(cargo.departure, true);
      allPoints.push(cargo.departure);
    }
    // Добавляем точку назначения
    if (!pointsMap.has(cargo.destination)) {
      pointsMap.set(cargo.destination, true);
      allPoints.push(cargo.destination);
    }
  }

  console.log("Building route through points:", allPoints);

  try {
    // Геокодируем все точки
    const geocodePromises = allPoints.map((point) => ymaps.geocode(point));
    const geocodeResults = await Promise.all(geocodePromises);

    // Получаем координаты всех точек
    const coordinates = geocodeResults.map((result) => {
      const geoObject = result.geoObjects.get(0);
      if (!geoObject) {
        throw new Error("Не удалось найти координаты для одной из точек");
      }
      return geoObject.geometry.getCoordinates();
    });

    console.log("Coordinates for route:", coordinates);

    // Строим единый оптимальный маршрут через все точки
    const multiRoute = new ymaps.multiRouter.MultiRoute(
      {
        referencePoints: coordinates,
        params: {
          results: 1,
          routingMode: "auto",
        },
      },
      {
        boundsAutoFit: true,
        wayPointStartIconColor: "#00FF00",
        wayPointFinishIconColor: "#FF0000",
        routeActiveStrokeWidth: 6,
        routeActiveStrokeColor: "#0000FF",
      },
    );

    myMap.geoObjects.add(multiRoute);

    // Ждем построения маршрута
    await new Promise((resolve) => {
      multiRoute.model.events.once("requestsuccess", resolve);
    });
  } catch (error) {
    console.error("Route building error:", error);
    alert(`Ошибка при построении маршрута: ${error.message}`);
    return;
  }
}

async function pickCar() {
  const cargos = await loadCargos(); // Get fresh data from API

  if (cargos.length === 0) {
    alert("Добавьте хотя бы один груз в список.");
    return;
  }

  // Маршрут уже построен, просто обновляем его
  await buildRoute();

  // Подбор машины через бэкенд
  try {
    console.log("Sending cargos to match:", cargos);
    const response = await fetch(`${API_URL}/match`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ cargos }),
    });
    console.log("Match response status:", response.status);
    if (!response.ok)
      throw new Error(`Ошибка подбора машины (status: ${response.status})`);
    const result = await response.json();
    console.log("Match result:", result);
    if (result.vehicle) {
      // Сохраняем данные в localStorage и перенаправляем на страницу подтверждения
      localStorage.setItem("selectedVehicleId", result.vehicle.id);
      localStorage.setItem("selectedCargos", JSON.stringify(cargos));

      // Перенаправление на страницу подтверждения
      window.location.href = "confirm.html";
    } else {
      alert(result.message || "Нет подходящей машины");
    }
  } catch (error) {
    console.error("Match error:", error);
    alert(`Ошибка подбора машины: ${error.message || "Неизвестная ошибка"}`);
  }
}

async function addToList() {
  const name = document.getElementById("name").value;
  const weight = parseFloat(document.getElementById("weight").value);
  const length = parseFloat(document.getElementById("length").value);
  const width = parseFloat(document.getElementById("width").value);
  const height = parseFloat(document.getElementById("height").value);
  const quantity = parseInt(document.getElementById("quantity").value);
  const departure = document.getElementById("departure").value;
  const destination = document.getElementById("destination").value;

  if (
    !name ||
    isNaN(weight) ||
    isNaN(length) ||
    isNaN(width) ||
    isNaN(height) ||
    isNaN(quantity) ||
    !departure ||
    !destination
  ) {
    alert("Пожалуйста, заполните все поля правильно.");
    return;
  }

  const formData = {
    name,
    weight,
    length,
    width,
    height,
    quantity,
    departure,
    destination,
  };

  try {
    const response = await fetch(`${API_URL}/cargos`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(formData),
    });
    if (!response.ok) throw new Error("Ошибка добавления груза");
    document.getElementById("name").value = "";
    document.getElementById("weight").value = "";
    document.getElementById("length").value = "";
    document.getElementById("width").value = "";
    document.getElementById("height").value = "";
    document.getElementById("quantity").value = "";
    document.getElementById("departure").value = "";
    document.getElementById("destination").value = "";
    await loadCargos(); // Refresh list

    // Прокладываем маршрут сразу после добавления груза
    await buildRoute();
  } catch (error) {
    alert(`Ошибка: ${error.message}`);
  }
}

function updateCargoList(cargos) {
  const tbody = document.getElementById("cargoTable").querySelector("tbody");
  tbody.innerHTML = "";

  cargos.forEach((cargo) => {
    let row = document.createElement("tr");
    row.innerHTML = `
      <td>${cargo.name}</td>
      <td>${cargo.weight}</td>
      <td>${cargo.length}</td>
      <td>${cargo.width}</td>
      <td>${cargo.height}</td>
      <td>${cargo.quantity}</td>
      <td>${cargo.departure}</td>
      <td>${cargo.destination}</td>
      <td><button onclick="removeCargo(${cargo.id})">Удалить</button></td>
    `;
    tbody.appendChild(row);
  });
}

async function removeCargo(id) {
  try {
    const response = await fetch(`${API_URL}/cargos/${id}`, {
      method: "DELETE",
    });
    if (!response.ok) throw new Error("Ошибка удаления груза");
    await loadCargos(); // Refresh list

    // Перестраиваем маршрут после удаления груза
    await buildRoute();
  } catch (error) {
    alert(`Ошибка: ${error.message}`);
  }
}
