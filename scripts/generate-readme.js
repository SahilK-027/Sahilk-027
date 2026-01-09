const fs = require('fs');
const path = require('path');

const projectsData = JSON.parse(fs.readFileSync('projects-data.json', 'utf8'));
const readmePath = 'README.md';
const readme = fs.readFileSync(readmePath, 'utf8');

function generateProjectsTable(projects) {
  const reversed = [...projects].reverse();
  const rows = [];
  const shimmerCell = `
      <td align="center">
        <img src="assets/thumbs/shimmer-placeholder.svg" width="280" alt="Coming Soon"/>
        <span>⎯⎯⎯⎯</span>
        <br/>
        <strong>Coming Soon</strong><br/>
        <span style="color: #768390;">Stay tuned!</span>
        &nbsp;
      </td>`;        

  for (let i = 0; i < reversed.length; i += 3) {
    const rowProjects = reversed.slice(i, i + 3);
    const cells = rowProjects
      .map((p) => {
        const links = [
          p.codeUrl ? `<a href="${p.codeUrl}">Code</a>` : null,
          p.liveUrl ? `<a href="${p.liveUrl}">Live</a>` : null,
        ]
          .filter(Boolean)
          .join(' · ');

        const thumbnail = p.liveUrl
          ? `<a href="${p.liveUrl}"><img src="${p.thumbnail}" width="280" alt="${p.title}"/></a>`
          : `<img src="${p.thumbnail}" width="280" alt="${p.title}"/>`;

        return `
      <td align="center">
        ${thumbnail}
        <span>⎯⎯⎯⎯</span>
        <br/>
        <strong>${p.title}</strong><br/>
        ${links}
      </td>`;
      })
      .join('');

    // Fill empty cells with shimmer placeholders
    const emptyCells = 3 - rowProjects.length;
    const fillerCells = shimmerCell.repeat(emptyCells);

    rows.push(`  <tr>${cells}${fillerCells}\n  </tr>`);
  }
  return `<table>\n${rows.join('\n')}\n</table>`;
}

const tableHtml = generateProjectsTable(projectsData.projects);
const projectCount = projectsData.projects.length;
const headerHtml = `## Projects <sup>${projectCount}</sup> ↘`;
const startMarker = '<!-- PROJECT-TABLE-START -->';
const endMarker = '<!-- PROJECT-TABLE-END -->';

let newReadme;
if (readme.includes(startMarker) && readme.includes(endMarker)) {
  newReadme = readme.replace(
    new RegExp(`${startMarker}[\\s\\S]*${endMarker}`),
    `${startMarker}\n${headerHtml}\n\n${tableHtml}\n${endMarker}`
  );
} else {
  console.error(
    'Missing markers in README.md. Add <!-- PROJECT-TABLE-START --> and <!-- PROJECT-TABLE-END --> where you want the table.'
  );
  process.exit(1);
}

fs.writeFileSync(readmePath, newReadme);
console.log('README.md updated successfully!');
