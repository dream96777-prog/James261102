const root = document.documentElement;

function setupTheme() {
  document.getElementById('theme-toggle').addEventListener('click', () => {
    const systemDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const current = root.dataset.theme || (systemDark ? 'dark' : 'light');
    const next = current === 'dark' ? 'light' : 'dark';
    root.dataset.theme = next;
    try {
      localStorage.setItem('theme', next);
    } catch (e) {
      // 저장할 수 없어도 현재 화면의 테마는 바뀐다.
    }
  });
}

function setupNav() {
  const toggle = document.getElementById('nav-toggle');
  const menu = document.getElementById('nav-menu');

  const setOpen = (open) => {
    menu.classList.toggle('open', open);
    toggle.setAttribute('aria-expanded', String(open));
    toggle.setAttribute('aria-label', open ? '메뉴 닫기' : '메뉴 열기');
  };

  toggle.addEventListener('click', () => setOpen(!menu.classList.contains('open')));
  menu.addEventListener('click', (event) => {
    if (event.target.closest('a')) setOpen(false);
  });
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') setOpen(false);
  });
}

function copyWithSelection(text) {
  const input = document.createElement('textarea');
  input.value = text;
  input.style.position = 'fixed';
  input.style.opacity = '0';
  document.body.append(input);
  input.select();
  const copied = document.execCommand('copy');
  input.remove();
  return copied;
}

function setupCopyEmail() {
  const button = document.getElementById('copy-email');
  const status = document.getElementById('copy-status');

  button.addEventListener('click', async () => {
    const email = button.dataset.email;
    let copied = false;
    try {
      await navigator.clipboard.writeText(email);
      copied = true;
    } catch (e) {
      copied = copyWithSelection(email);
    }
    status.textContent = copied
      ? '이메일 주소를 복사했습니다.'
      : '복사하지 못했습니다. 주소를 직접 선택해 복사해 주세요.';
  });
}

function createProjectCard(project) {
  const card = document.createElement('article');
  card.className = 'project-card';

  const image = document.createElement('img');
  image.src = project.image;
  image.alt = project.imageAlt;
  image.width = 640;
  image.height = 360;
  image.loading = 'lazy';

  const body = document.createElement('div');
  body.className = 'project-body';

  const title = document.createElement('h3');
  title.textContent = project.title;

  const description = document.createElement('p');
  description.textContent = project.description;

  const tags = document.createElement('ul');
  tags.className = 'tag-list';
  project.tech.forEach((tech) => {
    const tag = document.createElement('li');
    tag.textContent = tech;
    tags.append(tag);
  });

  body.append(title, description, tags);

  if (project.link) {
    const link = document.createElement('a');
    link.className = 'project-link';
    link.href = project.link;
    link.textContent = '자세히 보기';
    link.setAttribute('aria-label', `${project.title} 자세히 보기`);
    body.append(link);
  }

  card.append(image, body);
  return card;
}

function renderProjects(projects, list) {
  list.replaceChildren(...projects.map(createProjectCard));
}

function renderFilters(projects, container, list) {
  const techs = [...new Set(projects.flatMap((project) => project.tech))];
  const buttons = ['전체', ...techs].map((tech, index) => {
    const button = document.createElement('button');
    button.className = 'filter-button';
    button.type = 'button';
    button.textContent = tech;
    button.setAttribute('aria-pressed', String(index === 0));
    button.addEventListener('click', () => {
      buttons.forEach((other) => other.setAttribute('aria-pressed', String(other === button)));
      renderProjects(
        index === 0 ? projects : projects.filter((project) => project.tech.includes(tech)),
        list,
      );
    });
    return button;
  });
  container.replaceChildren(...buttons);
}

async function setupProjects() {
  const list = document.getElementById('project-list');
  const filters = document.getElementById('project-filters');

  try {
    const response = await fetch('data/projects.json');
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const projects = await response.json();
    renderFilters(projects, filters, list);
    renderProjects(projects, list);
  } catch (e) {
    const message = document.createElement('p');
    message.className = 'project-message';
    message.textContent = '프로젝트 목록을 불러오지 못했습니다. index.html을 직접 열었다면 로컬 서버로 실행해 주세요.';
    list.replaceChildren(message);
  }
}

setupTheme();
setupNav();
setupCopyEmail();
setupProjects();
