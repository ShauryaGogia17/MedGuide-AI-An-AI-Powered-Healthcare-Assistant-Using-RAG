export function formatNumber(value){return typeof value==='number'?new Intl.NumberFormat('en',{maximumSignificantDigits:15}).format(value):'—';}
export function formatPercent(value){return typeof value==='number'?new Intl.NumberFormat('en',{maximumFractionDigits:2}).format(value):'—';}
