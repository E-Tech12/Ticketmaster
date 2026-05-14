async function loadEvents(){

    const response = await fetch('/search')
    const events = await response.json()

    const container = document.getElementById("events")

    events.forEach(event => {

        container.innerHTML += `
            <div class="card">
                <img src="${event.image}">
                <h2>${event.name}</h2>
                <p>${event.date}</p>

                <button>
                    View Tickets
                </button>
            </div>
        `
    })
}

loadEvents()