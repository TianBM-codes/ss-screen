<script>
  import { onMount } from 'svelte'
  import { Structure } from 'matterviz/structure'
  import { open_material } from 'matterviz/file-viewer/open'

  let structure = null

  let title = '请选择结构文件'
  let message = '支持 pymatgen JSON、POSCAR、CONTCAR、CIF 和 XYZ。'

  // SS-Screen JSON switch cache: reuse the parsed data and the mounted viewer.
  let latestLoadId = 0
  const parsedStructures = new Map()
  const MAX_CACHED = 4

  window.ssScreenLoadStructure = async (
    content,
    filename = 'structure.json',
    label = filename,
  ) => {
    const id = ++latestLoadId
    try {
      const cached = parsedStructures.get(filename)
      let nextStructure
      if (cached && cached.content === content) {
        // Updating the same structure twice need not re-run the parser.
        nextStructure = cached.structure
        parsedStructures.delete(filename)
        parsedStructures.set(filename, cached)
      } else {
        const opened = await open_material({ data: content, filename })
        if (id !== latestLoadId) return  // A more recent selection won.
        if (opened.type !== 'structure') {
          structure = null
          title = label
          message = 'MatterViz could not recognize this structure.'
          return
        }
        nextStructure = opened.data
        parsedStructures.delete(filename)
        parsedStructures.set(filename, { content, structure: nextStructure })
        while (parsedStructures.size > MAX_CACHED) {
          parsedStructures.delete(parsedStructures.keys().next().value)
        }
      }
      if (id !== latestLoadId) return
      structure = nextStructure  // Reactive prop update; no component remount.
      title = label
      message = ''
    } catch (error) {
      if (id !== latestLoadId) return
      structure = null
      title = label
      message = `Structure load failed: ${error?.message ?? error}`
      console.error('SSSCREEN_STRUCTURE_LOAD_ERROR', error)
    }
  }

  window.ssScreenClearStructure = () => {
    latestLoadId += 1
    structure = null
    title = '请选择结构文件'
    message = '支持 pymatgen JSON、POSCAR、CONTCAR、CIF 和 XYZ。'
  }

  window.ssScreenMatterVizReady = true

  onMount(async () => {
    if (new URLSearchParams(window.location.search).get('demo') !== '1') return

    try {
      const response = await fetch('./demo-CaSe.json')
      if (!response.ok) throw new Error(`HTTP ${response.status}`)
      await window.ssScreenLoadStructure(
        await response.text(),
        'demo-CaSe.json',
        'CaSe 演示结构',
      )
    } catch (error) {
      message = `演示结构加载失败：${error?.message ?? error}`
    }
  })
</script>

<main>
  <header>
    <strong>{title}</strong>
    <span>MatterViz 0.7.0</span>
  </header>
  <section>
    {#if structure}
	  <Structure
		  {structure}
		  show_controls={false}
		  style="width: 100%; height: 100%;"
		/>
	{:else}
      <div class="empty">{message}</div>
    {/if}
  </section>
</main>
