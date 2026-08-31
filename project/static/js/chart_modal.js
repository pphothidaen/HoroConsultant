class ChartModal {
  constructor() {
    this.container = document.getElementById('chart-modal-container');
    if (!this.container) {
      console.warn("ChartModal container not found");
      return;
    }
    
    this.modalEl = document.createElement('div');
    this.modalEl.className = 'chart-modal glass-card';
    this.modalEl.style.display = 'none';
    this.modalEl.style.position = 'fixed';
    this.modalEl.style.top = '10%';
    this.modalEl.style.left = '10%';
    this.modalEl.style.width = '80%';
    this.modalEl.style.height = '80%';
    this.modalEl.style.zIndex = '1000';
    this.modalEl.style.overflow = 'hidden';
    
    this.closeBtn = document.createElement('button');
    this.closeBtn.innerText = 'X';
    this.closeBtn.style.position = 'absolute';
    this.closeBtn.style.top = '10px';
    this.closeBtn.style.right = '10px';
    this.closeBtn.onclick = () => this.close();
    
    this.exportBtn = document.createElement('button');
    this.exportBtn.innerText = 'Export SVG';
    this.exportBtn.style.position = 'absolute';
    this.exportBtn.style.top = '10px';
    this.exportBtn.style.right = '50px';
    this.exportBtn.onclick = () => this.exportCurrent();
    
    this.titleEl = document.createElement('h2');
    this.titleEl.style.marginLeft = '20px';
    
    this.contentEl = document.createElement('div');
    this.contentEl.style.width = '100%';
    this.contentEl.style.height = '90%';
    this.contentEl.style.overflow = 'auto';
    
    this.modalEl.appendChild(this.titleEl);
    this.modalEl.appendChild(this.closeBtn);
    this.modalEl.appendChild(this.exportBtn);
    this.modalEl.appendChild(this.contentEl);
    this.container.appendChild(this.modalEl);
    
    this.currentSvg = '';
    this.currentTitle = '';
    
    this.initKeyboardShortcuts();
    this.registerClickHandlers();
  }
  
  open(svgContent, discipline, title) {
    this.currentSvg = svgContent;
    this.currentTitle = title || discipline;
    this.titleEl.innerText = this.currentTitle;
    this.contentEl.innerHTML = svgContent;
    this.modalEl.style.display = 'block';
    
    // Simple zoom/pan
    const svgEl = this.contentEl.querySelector('svg');
    if (svgEl) {
      let scale = 1;
      svgEl.addEventListener('wheel', (e) => {
        e.preventDefault();
        scale += e.deltaY * -0.01;
        scale = Math.min(Math.max(0.5, scale), 4);
        svgEl.style.transform = `scale(${scale})`;
      });
    }
  }
  
  close() {
    this.modalEl.style.display = 'none';
    this.contentEl.innerHTML = '';
  }
  
  exportCurrent() {
    if (!this.currentSvg) return;
    const blob = new Blob([this.currentSvg], {type: "image/svg+xml"});
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${this.currentTitle}.svg`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  }
  
  initKeyboardShortcuts() {
    window.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        this.close();
      }
    });
  }
  
  registerClickHandlers() {
    document.querySelectorAll('.chart-card').forEach(card => {
      card.addEventListener('click', (e) => {
        const svgContainer = card.querySelector('.chart-svg-container');
        if (svgContainer) {
          const titleEl = card.querySelector('h3');
          this.open(svgContainer.innerHTML, 'Chart', titleEl ? titleEl.innerText : 'Chart');
        }
      });
    });
  }
}

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  window.chartModal = new ChartModal();
});
