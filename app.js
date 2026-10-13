const viewer = document.querySelector('#shield');
const stage = document.querySelector('#stage');
const status = document.querySelector('#status');
const buttons = [...document.querySelectorAll('.material-control button')];
const loading = document.querySelector('#loading');
let ready = false;

function fail(message) {
  ready = false;
  buttons.forEach(button => { button.disabled = true; });
  stage.setAttribute('aria-busy', 'false');
  loading.hidden = true;
  document.querySelector('#viewer-error').textContent = message;
  document.querySelector('#viewer-error').hidden = false;
  status.textContent = 'No se pudieron preparar los controles.';
}
viewer.addEventListener('error', () => fail('No se pudo cargar el escudo 3D. Comprueba tu conexión y vuelve a cargar la página.'));
viewer.addEventListener('progress', event => {
  document.querySelector('#loading-text').textContent = `Cargando escudo… ${Math.round(event.detail.totalProgress * 100)} %`;
});

viewer.addEventListener('load', async () => {
  try {
    const wood = viewer.model.getMaterialByName('Madera');
    const steel = viewer.model.getMaterialByName('Acero');
    const bronze = viewer.model.getMaterialByName('Bronce');
    if (!wood || !steel || !bronze) throw new Error('Faltan materiales con los nombres esperados.');
    const pbr = wood.pbrMetallicRoughness;
    const original = {
      color: pbr.baseColorTexture.texture,
      orm: pbr.metallicRoughnessTexture.texture,
      normal: wood.normalTexture.texture,
      steelColor: [...steel.pbrMetallicRoughness.baseColorFactor],
      bronzeNormal: bronze.normalTexture.texture,
    };
    if (!original.color || !original.orm || !original.normal || !original.bronzeNormal) throw new Error('Faltan mapas PBR.');
    status.textContent = 'Preparando los acabados…';
    // Only public APIs in model-viewer 4.1.0. ORM uses G=roughness, B=metallic.
    const [color, orm, normal] = await Promise.all([
      'Madera_desgastada_BaseColor', 'Madera_desgastada_ORM', 'Madera_desgastada_Normal',
    ].map(name => viewer.createTexture(`assets/textures/${name}.png`)));
    if (!color || !orm || !normal) throw new Error('No se pudieron precargar los mapas alternativos.');
    let worn = false, dark = false, relief = true;
    document.querySelector('#wood-toggle').onclick = event => {
      worn = !worn;
      pbr.baseColorTexture.setTexture(worn ? color : original.color);
      pbr.metallicRoughnessTexture.setTexture(worn ? orm : original.orm);
      wood.normalTexture.setTexture(worn ? normal : original.normal);
      event.currentTarget.setAttribute('aria-pressed', String(worn));
      document.querySelector('#wood-state').textContent = worn ? 'Desgastada' : 'Limpia';
      document.querySelector('.swatch.wood').style.backgroundImage = `url('assets/textures/Madera_${worn ? 'desgastada' : 'limpia'}_BaseColor.png')`;
      status.textContent = worn ? 'Madera desgastada: color, rugosidad y relieve actualizados.' : 'Madera limpia: texturas originales restauradas.';
    };
    document.querySelector('#steel-toggle').onclick = event => {
      dark = !dark;
      steel.pbrMetallicRoughness.setBaseColorFactor(dark ? [.25, .29, .32, 1] : original.steelColor);
      event.currentTarget.setAttribute('aria-pressed', String(dark));
      document.querySelector('#steel-state').textContent = dark ? 'Oscuro' : 'Gris';
      status.textContent = `Acero ${dark ? 'oscuro' : 'gris'}: se conserva su acabado metálico.`;
    };
    document.querySelector('#bronze-toggle').onclick = event => {
      relief = !relief;
      bronze.normalTexture.setTexture(relief ? original.bronzeNormal : null);
      event.currentTarget.setAttribute('aria-pressed', String(relief));
      document.querySelector('#bronze-state').textContent = relief ? 'Activado' : 'Desactivado';
      status.textContent = `Relieve del bronce ${relief ? 'activado' : 'desactivado'}.`;
    };
    ready = true;
    buttons.forEach(button => { button.disabled = false; });
    loading.hidden = true;
    stage.setAttribute('aria-busy', 'false');
    status.textContent = 'Listo. Los tres acabados se pueden combinar.';
  } catch (error) {
    console.error('Preparación de materiales:', error);
    fail('No se pudieron preparar los materiales. Comprueba tu conexión y vuelve a cargar la página.');
  }
});

// Self-hosted fixed official distribution; a rejected import gets a visible error.
try {
  await import('./assets/vendor/model-viewer-4.1.0.min.js');
} catch (error) {
  console.error('Carga del visor:', error);
  fail('No se pudo iniciar el visor 3D. Recarga la página en un navegador actualizado.');
}
setTimeout(() => {
  if (!ready && document.querySelector('#viewer-error').hidden) fail('La carga está tardando demasiado. Comprueba tu conexión y vuelve a cargar la página.');
}, 60000);
