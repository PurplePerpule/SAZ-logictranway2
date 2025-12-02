ymaps.ready(init);

var myMap;

function init() {
  myMap = new ymaps.Map("map", {
    center: [54.54, 26.38],
    zoom: 10,
  });
  loadCargos();
}

const API_URL = window.location.protocol + "//" + window.location.hostname + ":8080";

async function loadCargos() {
  const res = await fetch(`${API_URL}/draft_cargos`);
  const data = await res.json();
  updateCargoList(data);
  buildRoute(data); // передаём
  return data;
}

async function buildRoute(cargos) {
  // ← принимаем, не грузим снова
  if (!cargos || cargos.length === 0) {
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
  if (cargos.length === 0) {
    return alert("Добавьте хотя бы один груз в список!");
  }

  const applicant = document.getElementById("applicant").value.trim();
  const department = document.getElementById("department").value.trim();
  const phone_number = document.getElementById("phone_number").value.trim();
  const tent_type = document.getElementById("tent_type").value;

  if (!applicant) {
    return alert("Укажите ФИО заявителя!");
  }
  if (!department) {
    return alert("Укажите отдел!");
  }

  if (!confirm("Отправить заявку диспетчеру?")) return;

  try {
    const res = await fetch(`${API_URL}/orders`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        applicant,
        department,
        phone_number: phone_number || null,
        tent_type,
      }),
    });

    if (res.ok) {
      alert("Заявка успешно отправлена диспетчеру!");
      document.getElementById("cargoForm").reset();
      document.getElementById("applicant").value = "";
      document.getElementById("department").value = "";
      document.getElementById("phone_number").value = "";
      myMap.geoObjects.removeAll();
      updateCargoList([]);
    } else {
      const err = await res.json();
      alert("Ошибка: " + (err.error || "сервер не отвечает"));
    }
  } catch (err) {
    alert("Нет связи с сервером");
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
  const formData = {
    name: document.getElementById("name").value,
    weight: parseFloat(document.getElementById("weight").value),
    length: parseFloat(document.getElementById("length").value),
    width: parseFloat(document.getElementById("width").value),
    height: parseFloat(document.getElementById("height").value),
    quantity: parseInt(document.getElementById("quantity").value),
    departure: document.getElementById("departure").value,
    destination: document.getElementById("destination").value,
  };

  // 💠 корректная проверка
  const {
    name,
    departure,
    destination,
    weight,
    length,
    width,
    height,
    quantity,
  } = formData;

  if (!name || !departure || !destination) {
    return alert("Введите название груза, пункт отправки и пункт назначения");
  }

  if ([weight, length, width, height, quantity].some((v) => isNaN(v))) {
    return alert("Числовые поля заполнены неверно");
  }

  await fetch(`${API_URL}/draft_cargos`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(formData),
  });

  document.getElementById("cargoForm").reset();
  loadCargos();
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
  await fetch(`${API_URL}/draft_cargos/${id}`, { method: "DELETE" });
  loadCargos();
}
