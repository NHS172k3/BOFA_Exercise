const eventSlider = document.getElementById("eventSlider");
const eventInput = document.getElementById("eventInput");
const bondsBody = document.getElementById("bondsBody");
const pnlBody = document.getElementById("pnlBody");
const deskPvBody = document.getElementById("deskPvBody");
const traderPvBody = document.getElementById("traderPvBody");
const eventImpactText = document.getElementById("eventImpactText");
const fromEventInput = document.getElementById("fromEventInput");
const runPnlBtn = document.getElementById("runPnlBtn");
const bondIdInput = document.getElementById("bondIdInput");
const runBondQueryBtn = document.getElementById("runBondQueryBtn");
const bondQueryResult = document.getElementById("bondQueryResult");

const prevBtn = document.getElementById("prevBtn");
const nextBtn = document.getElementById("nextBtn");

const BONDS = ["BOND1", "BOND2", "BOND3", "BOND4", "BOND5"];
let currentEventId = Number(eventSlider.value);

function money(v) {
  return Number(v).toLocaleString(undefined, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

async function loadSnapshot(eventId) {
  const [snapshotRes, rollupsRes] = await Promise.all([
    fetch(`/api/snapshot?event=${eventId}`),
    fetch(`/api/rollups?event=${eventId}`),
  ]);

  const snapshotData = await snapshotRes.json();
  const rollupsData = await rollupsRes.json();

  const e = snapshotData.event_impact;
  eventImpactText.textContent = `#${e.event_id} | ${e.desk} | ${e.trader} | ${e.bond_id} | ${e.buy_sell} ${e.quantity} @ ${money(e.clean_price)} | Total PV ${money(snapshotData.summary.total_pv)} | dPV ${money(snapshotData.summary.delta_pv)}`;

  const bondMap = new Map(rollupsData.bond.map((b) => [b.bond_id, b]));
  const rows = BONDS.map((bondId) => {
    const b = bondMap.get(bondId);
    return {
      bond_id: bondId,
      quantity: b?.quantity ?? 0,
      clean_price: b?.clean_price ?? 0,
      accrued_interest: b?.accrued_interest ?? 0,
      dirty_price: b?.dirty_price ?? 0,
      present_value: b?.present_value ?? 0,
    };
  });

  bondsBody.innerHTML = rows
    .map(
      (row) =>
        `<tr>
          <td>${row.bond_id}</td>
          <td>${row.quantity}</td>
          <td>${money(row.clean_price)}</td>
          <td>${money(row.accrued_interest)}</td>
          <td>${money(row.dirty_price)}</td>
          <td>${money(row.present_value)}</td>
        </tr>`
    )
    .join("");

  deskPvBody.innerHTML = rollupsData.desk
    .map(
      (row) => `<tr><td>${row.desk}</td><td>${money(row.present_value)}</td></tr>`
    )
    .join("");

  traderPvBody.innerHTML = rollupsData.trader
    .map(
      (row) =>
        `<tr><td>${row.trader}</td><td>${row.desk}</td><td>${money(row.present_value)}</td></tr>`
    )
    .join("");
}

async function loadBondWisePnl(eventId) {
  const min = Number(fromEventInput.min || 1);
  const max = Number(fromEventInput.max || eventSlider.max);
  const safeFrom = Math.max(min, Math.min(max, Number(fromEventInput.value || 1)));
  fromEventInput.value = String(safeFrom);

  const res = await fetch(`/api/pnl-bond?from_event=${safeFrom}&event=${eventId}`);
  const data = await res.json();
  const bondMap = new Map(data.bonds.map((b) => [b.bond_id, b]));

  pnlBody.innerHTML = BONDS.map((bondId) => {
    const bond = bondMap.get(bondId);
    const pvCurrent = bond?.pv_current ?? 0;
    const pvBase = bond?.pv_base ?? 0;
    const pnl = bond?.pnl ?? 0;
    return `<tr>
      <td>${bondId}</td>
      <td>${money(pvCurrent)}</td>
      <td>${money(pvBase)}</td>
      <td>${money(pnl)}</td>
    </tr>`;
  }).join("");
}

async function runBondIdQuery() {
  const bondId = (bondIdInput.value || "").trim().toUpperCase();
  if (!bondId) {
    bondQueryResult.textContent = "Enter a Bond ID, for example BOND1.";
    return;
  }

  const res = await fetch(`/api/bond/${bondId}?event=${currentEventId}`);
  if (!res.ok) {
    bondQueryResult.textContent = `Query failed for ${bondId}.`;
    return;
  }

  const data = await res.json();
  bondQueryResult.textContent = `${bondId} at event ${currentEventId} -> PV ${money(data.present_value)} | Qty ${data.quantity}`;
}

function setEvent(eventId) {
  const min = Number(eventSlider.min);
  const max = Number(eventSlider.max);
  const safe = Math.max(min, Math.min(max, Number(eventId)));
  currentEventId = safe;
  eventSlider.value = String(safe);
  eventInput.value = String(safe);
  Promise.all([loadSnapshot(safe), loadBondWisePnl(safe)]);
}

eventSlider.addEventListener("input", () => setEvent(eventSlider.value));
eventInput.addEventListener("change", () => setEvent(eventInput.value));

prevBtn.addEventListener("click", () => setEvent(Number(eventSlider.value) - 1));
nextBtn.addEventListener("click", () => setEvent(Number(eventSlider.value) + 1));
runPnlBtn.addEventListener("click", () => setEvent(Number(eventSlider.value)));
runBondQueryBtn.addEventListener("click", runBondIdQuery);

setEvent(eventSlider.value);
