ymaps.ready(init);

var myMap;

// Проверка авторизации при загрузке страницы
document.addEventListener("DOMContentLoaded", function () {
  const token = localStorage.getItem("token");
  if (!token) {
    window.location.href = "login.html";
    return;
  }

  // Загружаем данные пользователя для автозаполнения
  fetch(`${API_URL}/me`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })
    .then((res) => (res.ok ? res.json() : null))
    .then((user) => {
      if (user) {
        if (!document.getElementById("applicant").value) {
          document.getElementById("applicant").value = user.full_name || "";
        }
        if (!document.getElementById("department").value) {
          document.getElementById("department").value = user.department || "";
        }
        if (!document.getElementById("phone_number").value) {
          document.getElementById("phone_number").value =
            user.phone_number || "";
        }
      }
    })
    .catch((err) => console.error("Ошибка загрузки данных пользователя:", err));

  // Загружаем сохраненные грузы
  loadCargos();
});

function init() {
  myMap = new ymaps.Map("map", {
    center: [54.54, 26.38],
    zoom: 10,
  });
  loadCargos();
}

const API_URL = "";

async function loadCargos() {
  const res = await fetch(`${API_URL}/draft_cargos`);
  const data = await res.json();
  updateCargoList(data);
  updateCargoCount(data.length);
  buildRoute(data); // передаём
  return data;
}

async function buildRoute(cargos) {
  myMap.geoObjects.removeAll();
  if (cargos.length === 0) return;

  // 1. База — откуда выезжает машина (берём departure из первого груза)
  const basePoint = cargos[0].departure;

  // 2. Все точки доставки (destination)
  const deliveryPoints = cargos.map((c) => c.destination);

  // 3. Формируем маршрут: база → все доставки → база
  const points = [basePoint, ...deliveryPoints, basePoint];

  try {
    const multiRoute = new ymaps.multiRouter.MultiRoute(
      {
        referencePoints: points,
        params: {
          routingMode: "auto",
          results: 1,
        },
      },
      {
        boundsAutoApply: true,
        routeStrokeColor: "0000FF",
        routeActiveStrokeColor: "FF0000",
        wayPointStartIconColor: "#00FF00",
        wayPointFinishIconColor: "#00FF00",
        viaPointIconColor: "#FFFF00",
      },
    );

    myMap.geoObjects.add(multiRoute);

    // Подписываемся на успешное построение
    multiRoute.model.events.add("requestsuccess", () => {
      myMap.setBounds(myMap.geoObjects.getBounds(), { checkZoomRange: true });
    });
  } catch (err) {
    console.error("Ошибка маршрута:", err);
    alert("Не удалось построить маршрут. Проверьте адреса.");
  }
}

async function sendOrderToDispatcher() {
  const cargos = await loadCargos();
  if (cargos.length === 0) {
    return alert("Добавьте хотя бы один груз в список!");
  }

  const token = localStorage.getItem("token");
  if (!token) {
    alert("Для отправки заявки необходимо войти в систему");
    window.location.href = "login.html";
    return;
  }

  // Получаем данные из полей формы
  const applicant = document.getElementById("applicant").value.trim();
  const department = document.getElementById("department").value.trim();
  const phone_number = document.getElementById("phone_number").value.trim();
  const tent_type = document.getElementById("tent_type").value;
  const preferred_date = document.getElementById("preferred_date").value;

  // ПРОВЕРКА ОБЯЗАТЕЛЬНЫХ ПОЛЕЙ
  if (!preferred_date) {
    alert("Пожалуйста, укажите желаемую дату отправления!");
    document.getElementById("preferred_date").focus();
    return;
  }

  if (!applicant) {
    alert("Укажите ФИО заявителя!");
    return;
  }
  if (!department) {
    alert("Укажите отдел!");
    return;
  }

  if (
    !confirm(
      `Отправить заявку диспетчеру?\n\nДата отправления: ${formatDate(preferred_date)}\nГрузов: ${cargos.length}\nЗаявитель: ${applicant}\nОтдел: ${department}`,
    )
  )
    return;

  try {
    const payload = {
      applicant,
      department,
      phone_number: phone_number || null,
      tent_type,
      preferred_departure_date: preferred_date, // Обязательно отправляем дату
    };

    console.log("Отправка заявки:", payload);

    const res = await fetch(`${API_URL}/orders`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.error || `Ошибка сервера: ${res.status}`);
    }

    const order = await res.json();
    alert(
      `Заявка #${order.id} успешно отправлена диспетчеру!\nДата: ${formatDate(preferred_date)}`,
    );

    // Сбрасываем только форму грузов и список, НО НЕ ДАТУ!
    document.getElementById("cargoForm").reset();
    myMap.geoObjects.removeAll();
    updateCargoList([]);
    updateCargoCount(0);

    // Можно спросить, хочет ли пользователь очистить дату для новой заявки
    if (confirm("Заявка отправлена. Хотите очистить дату для новой заявки?")) {
      document.getElementById("preferred_date").value = "";
    }
  } catch (error) {
    console.error("Ошибка отправки заявки:", error);
    alert("Ошибка: " + error.message);
  }
}

function formatDate(dateString) {
  if (!dateString) return "";
  const [year, month, day] = dateString.split("-");
  return `${day}.${month}.${year}`;
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

function clearAll() {
  if (!confirm("Очистить все поля формы? Это действие нельзя отменить.")) {
    return;
  }

  document.getElementById("cargoForm").reset();
  document.getElementById("applicant").value = "";
  document.getElementById("department").value = "";
  document.getElementById("phone_number").value = "";
  document.getElementById("preferred_date").value = "";
  myMap.geoObjects.removeAll();
  updateCargoList([]);
  updateCargoCount(0);

  // Установить сегодняшнюю дату по умолчанию
  const today = new Date().toISOString().split("T")[0];
  document.getElementById("preferred_date").value = today;

  alert("Все поля очищены. Дата установлена на сегодня.");
}

async function addToList() {
  const formData = {
    name: document.getElementById("name").value.trim(),
    weight: parseFloat(document.getElementById("weight").value),
    length: parseFloat(document.getElementById("length").value),
    width: parseFloat(document.getElementById("width").value),
    height: parseFloat(document.getElementById("height").value),
    quantity: parseInt(document.getElementById("quantity").value),
    departure: document.getElementById("departure").value.trim(),
    destination: document.getElementById("destination").value.trim(),
    tent_type: document.getElementById("tent_type").value,
  };

  // Проверка обязательных полей
  if (!formData.name || !formData.departure || !formData.destination) {
    alert("Заполните: название груза, пункт отправки и пункт назначения");
    return;
  }

  // Проверка числовых полей
  if (
    [
      formData.weight,
      formData.length,
      formData.width,
      formData.height,
      formData.quantity,
    ].some((v) => isNaN(v) || v <= 0)
  ) {
    alert("Числовые поля должны быть заполнены корректно (больше 0)");
    return;
  }

  try {
    const response = await fetch(`${API_URL}/draft_cargos`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${localStorage.getItem("token")}`,
      },
      body: JSON.stringify(formData),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || "Ошибка сервера");
    }

    document.getElementById("cargoForm").reset();
    await loadCargos();
  } catch (error) {
    console.error("Ошибка добавления груза:", error);
    alert("Ошибка: " + error.message);
  }
}

function updateCargoCount(count) {
  const countElement = document.getElementById("cargoCount");
  if (countElement) {
    countElement.textContent = count;
  }
}

function updateCargoList(cargos) {
  const tbody = document.getElementById("cargoTable").querySelector("tbody");
  if (!tbody) return;

  tbody.innerHTML = "";

  if (cargos.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="10" style="text-align: center; padding: 20px; color: #666;">
          Нет добавленных грузов
        </td>
      </tr>
    `;
    return;
  }

  cargos.forEach((cargo) => {
    const row = document.createElement("tr");
    const tentTypeText = cargo.tent_type === "open" ? "Открытый" : "Закрытый";
    const volume = (cargo.length * cargo.width * cargo.height).toFixed(2);
    const totalWeight = (cargo.weight * cargo.quantity).toFixed(1);

    row.innerHTML = `
      <td>${cargo.name}</td>
      <td>${cargo.weight} кг</td>
      <td>${cargo.length} м</td>
      <td>${cargo.width} м</td>
      <td>${cargo.height} м</td>
      <td>${cargo.quantity}</td>
      <td>${tentTypeText}</td>
      <td>${cargo.departure}</td>
      <td>${cargo.destination}</td>
      <td>
        <button onclick="removeCargo(${cargo.id})"
                style="background: #dc3545; color: white; border: none; padding: 5px 10px; border-radius: 3px; cursor: pointer;">
          Удалить
        </button>
      </td>
    `;
    tbody.appendChild(row);
  });
}

async function logout() {
  try {
    const token = localStorage.getItem("token");
    if (token) {
      await fetch(`${API_URL}/logout`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
    }
  } catch (error) {
    console.error("Ошибка при выходе:", error);
  } finally {
    localStorage.removeItem("token");
    // Очищаем все cookies
    document.cookie.split(";").forEach(function (c) {
      document.cookie = c
        .replace(/^ +/, "")
        .replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/");
    });
    window.location.href = "login.html";
  }
}

async function removeCargo(id) {
  if (!confirm("Удалить этот груз из заявки?")) return;

  try {
    const response = await fetch(`${API_URL}/draft_cargos/${id}`, {
      method: "DELETE",
      headers: {
        Authorization: `Bearer ${localStorage.getItem("token")}`,
      },
    });

    if (!response.ok) {
      throw new Error("Ошибка удаления груза");
    }

    await loadCargos();
  } catch (error) {
    console.error("Ошибка удаления груза:", error);
    alert("Не удалось удалить груз");
  }
}
