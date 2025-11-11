ymaps.ready(init);

var myMap;
let cargos = [];

function init() {
  myMap = new ymaps.Map("map", {
    center: [55.76, 37.64], // Координаты центра карты (Москва по умолчанию)
    zoom: 10,
  });
}

function pickCar() {
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

  Promise.all(routePromises).then(() => {
    // Симуляция подбора машины с учетом списка
    let totalWeight = cargos.reduce((sum, c) => sum + c.weight * c.quantity, 0);
    let totalQuantity = cargos.reduce((sum, c) => sum + c.quantity, 0);
    alert(
      `Маршруты построены для всех грузов. Общий вес: ${totalWeight} кг, Общее количество: ${totalQuantity}. Подбор машины... (Функциональность будет добавлена в будущем)`,
    );
  });
}

function addToList() {
  let name = document.getElementById("name").value;
  let weight = parseFloat(document.getElementById("weight").value);
  let length = parseFloat(document.getElementById("length").value);
  let width = parseFloat(document.getElementById("width").value);
  let quantity = parseInt(document.getElementById("quantity").value);
  let departure = document.getElementById("departure").value;
  let destination = document.getElementById("destination").value;

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

  cargos.push({
    name,
    weight,
    length,
    width,
    quantity,
    departure,
    destination,
  });
  updateCargoList();

  document.getElementById("name").value = "";
  document.getElementById("weight").value = "";
  document.getElementById("length").value = "";
  document.getElementById("width").value = "";
  document.getElementById("quantity").value = "";
  document.getElementById("departure").value = "";
  document.getElementById("destination").value = "";
}

function updateCargoList() {
  const tbody = document.getElementById("cargoTable").querySelector("tbody");
  tbody.innerHTML = "";

  cargos.forEach((cargo, index) => {
    let row = document.createElement("tr");
    row.innerHTML = `
      <td>${cargo.name}</td>
      <td>${cargo.weight}</td>
      <td>${cargo.length}</td>
      <td>${cargo.width}</td>
      <td>${cargo.quantity}</td>
      <td>${cargo.departure}</td>
      <td>${cargo.destination}</td>
      <td><button onclick="removeCargo(${index})">Удалить</button></td>
    `;
    tbody.appendChild(row);
  });
}

function removeCargo(index) {
  cargos.splice(index, 1);
  updateCargoList();
}
