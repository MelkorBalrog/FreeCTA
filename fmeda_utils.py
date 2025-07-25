from models import ASIL_ORDER, ASIL_TARGETS, component_fit_map


def compute_fmeda_metrics(entries, components, sg_to_asil, get_node=lambda x: x):
    """Return FMEDA metrics for the given failure modes."""
    comp_fit = component_fit_map(components)
    total = 0.0
    spf = 0.0
    lpf = 0.0
    asil = "QM"
    for be in entries:
        src = get_node(be)
        comp_name = src.parents[0].user_name if src.parents else getattr(src, "fmea_component", "")
        fit = comp_fit.get(comp_name)
        frac = getattr(src, "fmeda_fault_fraction", 0.0)
        if frac > 1.0:
            frac /= 100.0
        value = fit * frac if fit is not None else getattr(src, "fmeda_fit", 0.0)
        total += value
        if getattr(src, "fmeda_fault_type", "permanent") == "permanent":
            spf += value * (1 - getattr(src, "fmeda_diag_cov", 0.0))
        else:
            lpf += value * (1 - getattr(src, "fmeda_diag_cov", 0.0))
        sg = getattr(src, "fmeda_safety_goal", "")
        a = sg_to_asil(sg)
        if ASIL_ORDER.get(a, 0) > ASIL_ORDER.get(asil, 0):
            asil = a
    dc = (total - (spf + lpf)) / total if total else 0.0
    spfm_metric = 1 - spf / total if total else 0.0
    lpfm_metric = 1 - lpf / (total - spf) if total > spf else 0.0
    thresh = ASIL_TARGETS.get(asil, ASIL_TARGETS["QM"])
    return {
        "total": total,
        "spfm_raw": spf,
        "lpfm_raw": lpf,
        "dc": dc,
        "spfm_metric": spfm_metric,
        "lpfm_metric": lpfm_metric,
        "asil": asil,
        "ok_dc": dc >= thresh["dc"],
        "ok_spfm": spfm_metric >= thresh["spfm"],
        "ok_lpfm": lpfm_metric >= thresh["lpfm"],
    }
