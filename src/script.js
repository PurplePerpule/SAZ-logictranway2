ymaps.ready(init);

var myMap;

function init() {
  myMap = new ymaps.Map("map", {
    center: [55.76, 37.64], // Координаты центра карты (Москва по умолчанию)
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

async function pickCar() {
  const cargos = await loadCargos(); // Get fresh data from API

  if (cargos.length === 0) {
    alert("Добавьте хотя бы один груз в список.");
    return;
  }

  // Очистка предыдущих объектов на карте
  myMap.geoObjects.removeAll();

  // Построение маршрутов для каждого груза
  const routePromises = cargos.map((cargo) =>
    Promise.all([
      ymaps.geocode(cargo.departure),
      ymaps.geocode(cargo.destination),
    ])
      .then((results) => {
        const coordsA = results[0].geoObjects.get(0).geometry.getCoordinates();
        const coordsB = results[1].geoObjects.get(0).geometry.getCoordinates();

        const multiRoute = new ymaps.multiRouter.MultiRoute(
          {
            referencePoints: [coordsA, coordsB],
            params: {
              results: 1,
            },
          },
          {
            boundsAutoFit: true,
          },
        );

        myMap.geoObjects.add(multiRoute);
      })
      .catch((error) => {
        alert(
          `Ошибка при геокодировании для груза "${cargo.name}": ${error.message}`,
        );
      }),
  );

  await Promise.all(routePromises);

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
      alert(
        `Маршруты построены. Подходящая машина: ${result.vehicle.brand} (${result.vehicle.driver}), ёмкость ${result.vehicle.capacity} кг. Общий вес: ${result.total_weight} кг.`,
      );
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
  const quantity = parseInt(document.getElementById("quantity").value);
  const departure = document.getElementById("departure").value;
  const destination = document.getElementById("destination").value;

  if (
    !name ||
    isNaN(weight) ||
    isNaN(length) ||
    isNaN(width) ||
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
    document.getElementById("quantity").value = "";
    document.getElementById("departure").value = "";
    document.getElementById("destination").value = "";
    await loadCargos(); // Refresh list
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
  } catch (error) {
    alert(`Ошибка: ${error.message}`);
  }
}
