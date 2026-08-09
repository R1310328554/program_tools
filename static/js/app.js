(function () {
  function getCookie(name) {
    const match = document.cookie.match(new RegExp('(?:^|; )' + name.replace(/([.$?*|{}()[\]\\/+^])/g, '\\$1') + '=([^;]*)'));
    return match ? decodeURIComponent(match[1]) : '';
  }

  function ready(fn) {
    if (document.readyState !== 'loading') fn();
    else document.addEventListener('DOMContentLoaded', fn);
  }

  ready(function () {
    const page = document.querySelector('[data-tool-page]');
    if (!page) return;

    const slug = page.dataset.slug;
    const dual = page.dataset.dual === '1';
    const inputA = document.getElementById('input-a');
    const inputB = document.getElementById('input-b');
    const output = document.getElementById('output');
    const outputHtml = document.getElementById('output-html');
    const outputImage = document.getElementById('output-image');
    const status = document.getElementById('status');

    function collectOptions() {
      const opts = {};
      page.querySelectorAll('[data-opt]').forEach(function (el) {
        opts[el.dataset.opt] = el.value;
      });
      return opts;
    }

    function showText(text) {
      output.hidden = false;
      outputHtml.hidden = true;
      outputImage.hidden = true;
      output.value = text == null ? '' : String(text);
    }

    function showHtml(html) {
      output.hidden = true;
      outputImage.hidden = true;
      outputHtml.hidden = false;
      outputHtml.innerHTML = html;
      output.value = html;
    }

    function showImage(src) {
      output.hidden = true;
      outputHtml.hidden = true;
      outputImage.hidden = false;
      outputImage.innerHTML = '';
      const img = document.createElement('img');
      img.src = src;
      img.alt = 'generated output';
      outputImage.appendChild(img);
      output.value = src;
    }

    async function run(action) {
      status.textContent = '处理中…';
      status.className = 'status';
      try {
        const res = await fetch('/api/tools/' + slug + '/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
          },
          body: JSON.stringify({
            action: action,
            text: inputA ? inputA.value : '',
            text_b: dual && inputB ? inputB.value : '',
            options: collectOptions(),
          }),
        });
        const data = await res.json();
        if (!data.ok) {
          status.textContent = data.error || '处理失败';
          status.className = 'status error';
          return;
        }
        if (data.image) showImage(data.result);
        else if (data.html) showHtml(data.result);
        else showText(data.result);
        status.textContent = data.meta || '完成';
        status.className = 'status ok';
      } catch (err) {
        status.textContent = String(err);
        status.className = 'status error';
      }
    }

    page.querySelectorAll('[data-action]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        run(btn.dataset.action);
      });
    });

    const copyBtn = page.querySelector('[data-copy]');
    if (copyBtn) {
      copyBtn.addEventListener('click', async function () {
        try {
          await navigator.clipboard.writeText(output.value || '');
          status.textContent = '已复制到剪贴板';
          status.className = 'status ok';
        } catch (e) {
          status.textContent = '复制失败';
          status.className = 'status error';
        }
      });
    }

    const clearBtn = page.querySelector('[data-clear]');
    if (clearBtn) {
      clearBtn.addEventListener('click', function () {
        if (inputA) inputA.value = '';
        if (inputB) inputB.value = '';
        showText('');
        status.textContent = '';
        status.className = 'status';
      });
    }

    const swapBtn = page.querySelector('[data-swap]');
    if (swapBtn) {
      swapBtn.addEventListener('click', function () {
        if (!inputA) return;
        const tmp = inputA.value;
        inputA.value = output.value || '';
        showText(tmp);
      });
    }
  });
})();
