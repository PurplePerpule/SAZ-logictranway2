ymaps.ready(init);

var myMap;

function init() {
  myMap = new ymaps.Map("map", {
    center: [54.54, 26.38],
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

async function buildRoute() {
  const cargos = await loadCargos();
  if (cargos.length === 0) {
    myMap.geoObjects.removeAll();
    return;
  }
  myMap.geoObjects.removeAll();
  const allPoints = [];
  const pointsMap = new Map();
  for (const cargo of cargos) {
    if (!pointsMap.has(cargo.departure)) {
      pointsMap.set(cargo.departure, true);
      allPoints.push(cargo.departure);
    }
    if (!pointsMap.has(cargo.destination)) {
      pointsMap.set(cargo.destination, true);
      allPoints.push(cargo.destination);
    }
  }
  console.log("Building route through points:", allPoints);
  try {
    const geocodePromises = allPoints.map((point) => ymaps.geocode(point));
    const geocodeResults = await Promise.all(geocodePromises);
    const coordinates = geocodeResults.map((result) => {
      const geoObject = result.geoObjects.get(0);
      if (!geoObject) {
        throw new Error("Не удалось найти координаты для одной из точек");
      }
      return geoObject.geometry.getCoordinates();
    });
    console.log("Coordinates for route:", coordinates);
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
    await new Promise((resolve) => {
      multiRoute.model.events.once("requestsuccess", resolve);
    });
  } catch (error) {
    console.error("Route building error:", error);
    alert(`Ошибка при построении маршрута: ${error.message}`);
    return;
  }
}

async function sendOrderToDispatcher() {
  const cargos = await loadCargos();
  if (cargos.length === 0) return alert("Нет грузов");
  const applicant = document.getElementById("applicant").value;
  const department = document.getElementById("department").value;
  const phone_number = document.getElementById("phone_number").value;
  const tent_type = document.getElementById("tent_type").value;
  if (!applicant || !department) return alert("Заполните заявителя и отдел");
  if (confirm("Отправить заявку?")) {
    const res = await fetch(`${API_URL}/orders`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        cargos,
        applicant,
        department,
        phone_number,
        tent_type,
      }),
    });
    if (res.ok) {
      alert("Заявка отправлена!");
      document.getElementById("applicant").value = "";
      document.getElementById("department").value = "";
      document.getElementById("phone_number").value = "";
    } else {
      alert("Ошибка");
    }
  }
}

async function pickCar() {
  const cargos = await loadCargos();
  if (cargos.length === 0) {
    alert("Добавьте хотя бы один груз в список.");
    return;
  }
  await buildRoute();
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
      localStorage.setItem("selectedVehicleId", result.vehicle.id);
      localStorage.setItem("selectedCargos", JSON.stringify(cargos));
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
    await loadCargos();
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
    await loadCargos();
    await buildRoute();
  } catch (error) {
    alert(`Ошибка: ${error.message}`);
  }
}
