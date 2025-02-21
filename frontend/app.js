const baseUrl = "http://localhost:8000";

// Función para convertir Markdown a HTML
function convertMarkdownToHTML(markdown) {
    const lines = markdown.split('\n');
    let html = "";
    let inList = false;
    
    lines.forEach((line) => {
        const trimmed = line.trim();
        if (trimmed.startsWith("* ")) {
            if (!inList) {
                html += "<ul>";
                inList = true;
            }
            const item = trimmed.substring(2).trim();
            html += `<li>${item}</li>`;
        } else {
            if (inList) {
                html += "</ul>";
                inList = false;
            }
            // Procesa bold (**texto**) e italic (*texto*)
            let processedLine = line.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
            processedLine = processedLine.replace(/\*(.*?)\*/g, "<em>$1</em>");
            if (processedLine.trim() !== "") {
                html += `<p>${processedLine}</p>`;
            }
        }
    });
    
    if (inList) {
        html += "</ul>";
    }
    return html;
}

// Función para mostrar resultados en un div específico
function showResult(elementId, message) {
    document.getElementById(elementId).innerHTML = message;
}

// Agregar Misión Manual
document.getElementById("addMissionForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const title = document.getElementById("title").value;
    const description = document.getElementById("description").value;
    
    try {
        const response = await fetch(`${baseUrl}/add_mission/`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ title, description })
        });
        const data = await response.json();
        showResult("addMissionResult", `<strong>${data.message}</strong> (ID: ${data.mission_id})`);
    } catch (error) {
        showResult("addMissionResult", "❌ Error al agregar la misión.");
    }
});

// Buscar Misión
document.getElementById("searchMissionForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const query = document.getElementById("searchQuery").value;
    
    try {
        const response = await fetch(`${baseUrl}/search_mission/?query=${encodeURIComponent(query)}`);
        const data = await response.json();
        if (data.results && data.results.length > 0) {
            let html = "<ul>";
            data.results.forEach(mission => {
                html += `<li><strong>${mission.title}</strong>: ${mission.description}</li>`;
            });
            html += "</ul>";
            showResult("searchResult", html);
        } else {
            showResult("searchResult", "No se encontraron misiones.");
        }
    } catch (error) {
        showResult("searchResult", "❌ Error al buscar misiones.");
    }
});

// Generar Misión con LLM y mostrar salida formateada
document.getElementById("generateMissionForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const query = document.getElementById("generateQuery").value;
    
    try {
        const response = await fetch(`${baseUrl}/generate_mission/`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ query })
        });
        if (!response.ok) throw new Error("Error en la solicitud");
        const data = await response.json();

        if (data.mission) {
            // Convertir el Markdown de la descripción a HTML
            const formattedDescription = convertMarkdownToHTML(data.mission.description);
            const resultHTML = `
                <h3>¡Misión Generada!</h3>
                <p><strong>Título:</strong> ${data.mission.title}</p>
                <div>
                    <strong>Detalles:</strong><br>
                    ${formattedDescription}
                </div>
            `;
            showResult("generateResult", resultHTML);
        } else {
            showResult("generateResult", "No se pudo generar la misión.");
        }
    } catch (error) {
        showResult("generateResult", "❌ Error al generar la misión.");
        console.error("Error:", error);
    }
});
