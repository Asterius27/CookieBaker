// Code snippet used to scrape Awesome-Selfhosted

const sections = document.querySelectorAll('section');

let projects = [];

sections.forEach(section => {
    const name = section.querySelector('h3')?.childNodes[0]?.textContent.trim() || '';
    const sourceLink = [...section.querySelectorAll('a')]
        .find(a => a.textContent.toLowerCase().includes('source code'))?.href || '';

    const platforms = [...section.querySelectorAll('.platform a')]
        .map(a => a.textContent.trim())
        .sort((a, b) => a.localeCompare(b)); // A–Z

    projects.push({
        name,
        sourceLink,
        platforms
    });
});

let ris = "";
for (let p of projects) {
    ris += p.name + "\t" + p.sourceLink + "\t" + p.platforms.join("\t") + "\n";
}

console.log(ris);
