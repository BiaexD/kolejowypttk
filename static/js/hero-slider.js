(function(){
  const root = document.querySelector('.hero-slider');
  if(!root) return;
  const slides = Array.from(root.querySelectorAll('.slide'));
  const dots   = Array.from(root.querySelectorAll('.dot'));
  if(slides.length <= 1) return;

  let i = 0;
  const dur = parseInt(root.getAttribute('data-interval') || '5000', 10);

  function go(n){
    slides[i].classList.remove('is-active');
    if(dots[i]) dots[i].classList.remove('is-active');
    i = (n + slides.length) % slides.length;
    slides[i].classList.add('is-active');
    if(dots[i]) dots[i].classList.add('is-active');
  }
  let timer = setInterval(()=>go(i+1), dur);

  dots.forEach((d, idx)=>{
    d.addEventListener('click', ()=>{
      clearInterval(timer);
      go(idx);
      timer = setInterval(()=>go(i+1), dur);
    });
  });
})();
