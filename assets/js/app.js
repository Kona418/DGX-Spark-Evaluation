document.addEventListener('DOMContentLoaded', () => {
    const grid = document.getElementById('gallery-grid');
    const modal = document.getElementById('media-modal');
    const closeModal = document.querySelector('.close-modal');
    const modalMediaContainer = document.getElementById('modal-media-container');
    const modalTitle = document.getElementById('modal-title');
    const modalBadges = document.getElementById('modal-badges');
    const modalPromptText = document.getElementById('modal-prompt-text');

    // UI Controls
    const btnAll = document.querySelector('[data-filter="all"]');
    const btnImages = document.querySelector('[data-filter="type-image"]');
    const btnVideos = document.querySelector('[data-filter="type-video"]');
    
    const selectModel = document.getElementById('model-filter');
    const selectDuration = document.getElementById('duration-filter');
    const selectPrompt = document.getElementById('prompt-filter');

    // Populate categories dynamically based on data.js
    const uniqueCategories = [...new Set(mediaData.map(item => item.category))];
    uniqueCategories.sort().forEach(cat => {
        const option = document.createElement('option');
        option.value = cat;
        option.textContent = cat;
        selectPrompt.appendChild(option);
    });

    let currentFilters = {
        type: 'all',
        model: 'all',
        duration: 'all',
        prompt: 'all'
    };

    function updateDurationSelectState() {
        if (currentFilters.type === 'type-image') {
            selectDuration.disabled = true;
            selectDuration.value = 'all';
            currentFilters.duration = 'all';
        } else {
            selectDuration.disabled = false;
        }
    }

    function renderGrid(filters) {
        grid.innerHTML = '';
        
        const filteredData = mediaData.filter(item => {
            if (filters.type !== 'all') {
                if (filters.type === 'type-image' && item.type !== 'image') return false;
                if (filters.type === 'type-video' && item.type !== 'video') return false;
            }
            if (filters.model !== 'all' && item.model !== filters.model) return false;
            if (filters.duration !== 'all') {
                if (item.type === 'video' && item.duration !== filters.duration) return false;
            }
            if (filters.prompt !== 'all' && item.category !== filters.prompt) return false;
            return true;
        });

        filteredData.forEach((item, index) => {
            const card = document.createElement('div');
            card.className = 'gallery-item';
            card.dataset.index = index;

            let mediaHTML = '';
            if (item.type === 'video') {
                const thumbSrc = item.thumb ? item.thumb : item.file;
                
                if (item.thumb) {
                    mediaHTML = `<img src="${item.thumb}" loading="lazy" alt="${item.model} Video"/>`;
                } else {
                    mediaHTML = `<video src="${item.file}" preload="metadata"></video>`;
                }
                mediaHTML += `<div class="play-overlay">▶</div>`;
            } else {
                mediaHTML = `<img src="${item.thumb}" loading="lazy" alt="${item.model} Image"/>`;
            }

            let badgesHTML = `<span class="model-badge">${item.model}</span>`;
            if (item.type === 'video') {
                badgesHTML += `<span class="type-badge">${item.duration}s${item.duration === '15' ? ' +Audio' : ''}</span>`;
            }
            badgesHTML += `<span class="type-badge" style="background:#f39c12; color:#fff;">Seed: ${item.seed}</span>`;
            badgesHTML += `<span class="type-badge" style="background:#17a2b8; color:#fff;">${item.category}</span>`;


            card.innerHTML = `
                <div class="media-thumb">
                    ${mediaHTML}
                </div>
                <div class="meta">
                    <div class="meta-line">
                        <div style="display: flex; flex-wrap: wrap; gap: 4px;">${badgesHTML}</div>
                    </div>
                </div>
            `;
            
            card.addEventListener('click', () => openModal(item));
            grid.appendChild(card);
        });
    }

    function openModal(item) {
        modalMediaContainer.innerHTML = '';
        
        if (item.type === 'video') {
            const video = document.createElement('video');
            video.src = item.file;
            video.controls = true;
            video.autoplay = true;
            video.muted = (item.duration !== '15'); // Unmute if it's the 15s audio model
            modalMediaContainer.appendChild(video);
        } else {
            const img = document.createElement('img');
            img.src = item.file;
            modalMediaContainer.appendChild(img);
        }

        modalTitle.textContent = `${item.model}`;
        
        let badgesHTML = `<span class="model-badge">${item.model}</span>`;
        if (item.type === 'video') {
            badgesHTML += `<span class="type-badge">${item.duration}s${item.duration === '15' ? ' +Audio' : ''}</span>`;
        }
        badgesHTML += `<span class="type-badge" style="background:#f39c12; color:#fff;">Seed: ${item.seed}</span>`;
        badgesHTML += `<span class="type-badge" style="background:#17a2b8; color:#fff;">${item.category}</span>`;
        
        modalBadges.innerHTML = badgesHTML;
        
        modalPromptText.textContent = item.prompt;
        
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }

    function closeModalHandler() {
        modal.classList.remove('active');
        document.body.style.overflow = '';
        modalMediaContainer.innerHTML = ''; // Stop video playback
    }

    closeModal.addEventListener('click', closeModalHandler);
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeModalHandler();
        }
    });
    
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && modal.classList.contains('active')) {
            closeModalHandler();
        }
    });

    // Event Listeners for Filters
    function handleTypeBtnClick(e) {
        btnAll.classList.remove('active');
        btnImages.classList.remove('active');
        btnVideos.classList.remove('active');
        e.target.classList.add('active');
        currentFilters.type = e.target.dataset.filter;
        updateDurationSelectState();
        renderGrid(currentFilters);
    }

    btnAll.addEventListener('click', handleTypeBtnClick);
    btnImages.addEventListener('click', handleTypeBtnClick);
    btnVideos.addEventListener('click', handleTypeBtnClick);

    selectModel.addEventListener('change', (e) => {
        currentFilters.model = e.target.value;
        renderGrid(currentFilters);
    });

    selectDuration.addEventListener('change', (e) => {
        currentFilters.duration = e.target.value;
        renderGrid(currentFilters);
    });

    selectPrompt.addEventListener('change', (e) => {
        currentFilters.prompt = e.target.value;
        renderGrid(currentFilters);
    });

    // Initial render
    renderGrid(currentFilters);
});
