/** @odoo-module **/

import { Component, onMounted, onPatched, onWillStart, useRef, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useBus, useService } from "@web/core/utils/hooks";
import { Layout } from "@web/search/layout";
import { SearchBar } from "@web/search/search_bar/search_bar";
import { WithSearch } from "@web/search/with_search/with_search";
import { standardActionServiceProps } from "@web/webclient/actions/action_service";

/**
 * Extract partner / date filters from a sale.order search domain.
 * Other domain leaves are returned as soExtraDomain for SO-only filtering.
 */
function parseSalesDashboardDomain(domain = []) {
    let partnerId = false;
    let startDate = false;
    let endDate = false;
    const soExtraDomain = [];

    for (const leaf of domain) {
        if (!Array.isArray(leaf) || leaf.length < 3) {
            soExtraDomain.push(leaf);
            continue;
        }
        const [field, operator, value] = leaf;
        if (field === "partner_id" && ["=", "child_of", "in"].includes(operator)) {
            if (operator === "in" && Array.isArray(value) && value.length === 1) {
                partnerId = value[0];
            } else if (operator !== "in") {
                partnerId = value;
            } else {
                soExtraDomain.push(leaf);
            }
            continue;
        }
        if (field === "date_order") {
            const dateValue = typeof value === "string" ? value.slice(0, 10) : value;
            if (operator === ">=" || operator === ">") {
                startDate = dateValue;
                continue;
            }
            if (operator === "<=" || operator === "<") {
                endDate = dateValue;
                continue;
            }
        }
        soExtraDomain.push(leaf);
    }
    return { partnerId, startDate, endDate, soExtraDomain };
}

export class SalesDashboard extends Component {
    static template = "sales_customization.SalesDashboard";
    static components = { Layout, SearchBar };
    static props = {
        "*": true,
    };

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({
            loading: true,
            data: null,
            showDetail: false,
            detail: null,
        });
        this._filters = {
            partnerId: false,
            startDate: false,
            endDate: false,
            soExtraDomain: [],
        };
        this._chartsSignature = null;
        this._lastDetailToken = null;
        this._lastDetailAt = 0;
        this.soChartRef = useRef("soChart");
        this.invChartRef = useRef("invChart");
        this.oldChartRef = useRef("oldChart");
        this.payChartRef = useRef("payChart");
        this.topChartRef = useRef("topChart");
        this.itemsChartRef = useRef("itemsChart");
        this.catChartRef = useRef("catChart");
        this.containerChartRef = useRef("containerChart");
        this.agingChartRef = useRef("agingChart");
        this.salespersonChartRef = useRef("salespersonChart");
        this.brandChartRef = useRef("brandChart");
        this.countryChartRef = useRef("countryChart");
        this.portChartRef = useRef("portChart");
        this.paidOpenChartRef = useRef("paidOpenChart");
        this.refundChartRef = useRef("refundChart");
        this.marginChartRef = useRef("marginChart");
        this.cohortChartRef = useRef("cohortChart");
        this.termsChartRef = useRef("termsChart");
        this._charts = [];

        useBus(this.env.searchModel, "update", () => {
            this._loadData();
        });

        onWillStart(async () => {
            await this._loadData();
        });

        onMounted(() => this._renderCharts());
        onPatched(() => this._renderCharts());
    }

    get display() {
        return {
            ...(this.props.display || {}),
            controlPanel: this.props.display?.controlPanel ?? {},
            searchPanel: false,
        };
    }

    async _loadData() {
        const domain = this.env.searchModel?.domain || this.props.domain || [];
        const { partnerId, startDate, endDate, soExtraDomain } = parseSalesDashboardDomain(domain);
        const contextPartnerId = this.props.context?.partner_id || false;
        const normalizedPartnerId = partnerId || contextPartnerId || false;

        this._filters = {
            partnerId: normalizedPartnerId || false,
            startDate: startDate || false,
            endDate: endDate || false,
            soExtraDomain: soExtraDomain || [],
        };
        this.state.loading = true;
        this._destroyCharts();
        this.state.data = await this.orm.call(
            "res.partner",
            "get_sales_dashboard_data",
            [
                this._filters.partnerId,
                this._filters.startDate,
                this._filters.endDate,
                this._filters.soExtraDomain,
            ]
        );
        this.state.loading = false;
    }

    closeDetail() {
        this.state.showDetail = false;
        this.state.detail = null;
    }

    onDetailOverlayClick(ev) {
        if (ev.target === ev.currentTarget) {
            this.closeDetail();
        }
    }

    async openKpiDetails(chartKey) {
        await this._fetchDetails(chartKey, {});
    }

    async _onDataPoint(chartKey, config) {
        if (config?.dataPointIndex == null || config.dataPointIndex < 0) {
            return;
        }
        const token = `${chartKey}:${config.seriesIndex}:${config.dataPointIndex}`;
        const now = Date.now();
        if (this._lastDetailToken === token && now - this._lastDetailAt < 400) {
            return;
        }
        this._lastDetailToken = token;
        this._lastDetailAt = now;
        await this._fetchDetails(chartKey, this._buildPoint(chartKey, config));
    }

    _buildPoint(chartKey, config) {
        const data = this.state.data || {};
        const idx = config.dataPointIndex;
        const seriesIndex = config.seriesIndex;
        const monthKeys = data.month_keys || [];
        const labels = data.labels || [];
        const point = {
            index: idx,
            series_index: seriesIndex,
            month_key: monthKeys[idx] || false,
            label: labels[idx] || false,
            series_name: false,
            id: false,
            name: false,
            key: false,
            value: 0,
        };
        const seriesNameByChart = {
            sale_orders: seriesIndex === 0 ? "count" : "total",
            sale_invoices: seriesIndex === 0 ? "count" : "total",
            old_sales: seriesIndex === 0 ? "count" : "total",
            paid_open: seriesIndex === 0 ? "paid" : "open",
            cohort: seriesIndex === 0 ? "new" : "returning",
            refunds: "total",
            margin: "total",
        };
        if (seriesNameByChart[chartKey]) {
            point.series_name = seriesNameByChart[chartKey];
        }
        if (chartKey === "paid_open") {
            point.label = (data.series?.paid_open?.labels || labels)[idx] || false;
        }
        if (chartKey === "cohort") {
            point.label = (data.series?.cohort?.labels || labels)[idx] || false;
        }
        const rowMap = {
            top_customers: data.top_customers,
            top_items: data.top_items,
            top_categories: data.top_categories,
            salesperson: data.sales_by_salesperson,
            brand: data.sales_by_brand,
            country: data.sales_by_country,
            port: data.sales_by_port,
            payment_terms: data.payment_terms,
            payment_states: data.payment_states,
            container_types: data.container_types,
        };
        const rows = rowMap[chartKey];
        if (rows?.[idx]) {
            const row = rows[idx];
            point.id = row.id || false;
            point.name = row.name || row.label || false;
            point.key = row.key || false;
            point.value = row.total || row.value || 0;
            point.label = point.name;
        }
        if (chartKey === "aging") {
            const keys = Object.keys(data.aging_buckets || {});
            point.key = keys[idx] || false;
            point.name = point.key;
            point.label = point.key;
            point.value = data.aging_buckets?.[point.key] || 0;
        }
        return point;
    }

    async _fetchDetails(chartKey, point) {
        this.state.showDetail = true;
        this.state.detail = { loading: true, title: "Loading details..." };
        try {
            this.state.detail = await this.orm.call(
                "res.partner",
                "get_sales_dashboard_details",
                [
                    chartKey,
                    point || {},
                    this._filters.partnerId,
                    this._filters.startDate,
                    this._filters.endDate,
                    this._filters.soExtraDomain,
                ]
            );
        } catch (_err) {
            this.state.detail = {
                title: "Details",
                explanation: "Unable to load the source records for this value.",
                loading: false,
                rows: [],
                count: 0,
                amount: 0,
            };
        }
    }

    async openDetailRecord(ev) {
        const detail = this.state.detail;
        const id = Number(ev.currentTarget.dataset.id);
        if (!detail?.model || !id) {
            return;
        }
        await this.action.doAction({
            type: "ir.actions.act_window",
            res_model: detail.model,
            res_id: id,
            views: [[false, "form"]],
            target: "new",
        });
    }

    async openAllDetailRecords() {
        const detail = this.state.detail;
        if (!detail?.model) {
            return;
        }
        await this.action.doAction({
            type: "ir.actions.act_window",
            name: detail.title || "Source Records",
            res_model: detail.model,
            domain: detail.domain || [],
            views: [[false, "list"], [false, "form"]],
            view_mode: "list,form",
            target: "current",
        });
    }

    _withClick(options, chartKey) {
        options.chart = options.chart || {};
        const prevEvents = options.chart.events || {};
        options.chart.events = {
            ...prevEvents,
            click: (event, ctx, config) => {
                prevEvents.click?.(event, ctx, config);
                this._onDataPoint(chartKey, config || {});
            },
            dataPointSelection: (event, ctx, config) => {
                prevEvents.dataPointSelection?.(event, ctx, config);
                this._onDataPoint(chartKey, config);
            },
            markerClick: (event, ctx, opts) => {
                prevEvents.markerClick?.(event, ctx, opts);
                this._onDataPoint(chartKey, opts || {});
            },
        };
        return options;
    }

    _destroyCharts() {
        for (const chart of this._charts) {
            try {
                chart.destroy();
            } catch (_err) {
                // best-effort cleanup
            }
        }
        this._charts = [];
        this._chartsSignature = null;
    }

    _renderCharts() {
        if (this.state.loading) {
            return;
        }
        if (!window.ApexCharts) {
            return;
        }
        const data = this.state.data;
        if (!data) {
            return;
        }
        if (this._chartsSignature === data && this._charts.length) {
            return;
        }
        this._destroyCharts();
        this._chartsSignature = data;

        const labels = data.labels || [];
        const charts = [
            {
                ref: this.soChartRef,
                key: "sale_orders",
                title: "Sales Orders",
                series: data.series.sale_orders,
            },
            {
                ref: this.invChartRef,
                key: "sale_invoices",
                title: "Sales Invoices",
                series: data.series.sale_invoices,
            },
            {
                ref: this.oldChartRef,
                key: "old_sales",
                title: "Historical (Old) Sales",
                series: data.series.old_sales,
            },
        ];

        for (const chart of charts) {
            if (!chart.ref.el) {
                continue;
            }
            const options = this._withClick(
                {
                    chart: {
                        type: "line",
                        height: 300,
                        toolbar: { show: false },
                        fontFamily: "Inter, system-ui, -apple-system, Segoe UI, sans-serif",
                    },
                    stroke: { width: [0, 3], curve: "smooth" },
                    dataLabels: { enabled: false },
                    grid: { strokeDashArray: 4, borderColor: "#e6e9ef" },
                    xaxis: {
                        categories: labels,
                        labels: { rotate: -35, style: { fontSize: "11px" } },
                    },
                    yaxis: [
                        {
                            title: { text: "Count" },
                            labels: { style: { fontSize: "11px" } },
                        },
                        {
                            opposite: true,
                            title: { text: "Amount" },
                            labels: {
                                formatter: (val) => {
                                    if (!val) return "0";
                                    const abs = Math.abs(val);
                                    if (abs >= 1_000_000) return `${(val / 1_000_000).toFixed(1)}M`;
                                    if (abs >= 1_000) return `${(val / 1_000).toFixed(1)}k`;
                                    return val.toFixed(0);
                                },
                                style: { fontSize: "11px" },
                            },
                        },
                    ],
                    series: [
                        {
                            name: `${chart.title} Count`,
                            type: "column",
                            data: chart.series?.count || [],
                        },
                        {
                            name: `${chart.title} Amount`,
                            type: "line",
                            data: chart.series?.total || [],
                        },
                    ],
                    colors: ["#5b8def", "#10b981"],
                    legend: { position: "top" },
                    tooltip: { shared: true },
                },
                chart.key
            );
            const instance = new window.ApexCharts(chart.ref.el, options);
            instance.render();
            this._charts.push(instance);
        }

        const namedBar = (ref, rows, chartKey, valueKey = "total") => {
            if (!ref.el || !rows?.length) {
                return;
            }
            const options = this._withClick(
                {
                    chart: { type: "bar", height: 300, toolbar: { show: false } },
                    plotOptions: { bar: { horizontal: true } },
                    dataLabels: { enabled: false },
                    grid: { strokeDashArray: 4, borderColor: "#e6e9ef" },
                    xaxis: { categories: rows.map((r) => r.name || r.label) },
                    series: [{ name: "Amount", data: rows.map((r) => r[valueKey] || r.value || 0) }],
                    colors: ["#5b8def"],
                },
                chartKey
            );
            const instance = new window.ApexCharts(ref.el, options);
            instance.render();
            this._charts.push(instance);
        };

        if (this.payChartRef.el && data.payment_states?.length) {
            const options = this._withClick(
                {
                    chart: { type: "donut", height: 300, toolbar: { show: false } },
                    labels: data.payment_states.map((r) => r.label),
                    series: data.payment_states.map((r) => r.value || 0),
                    legend: { position: "bottom" },
                    colors: ["#10b981", "#f59e0b", "#ef4444", "#6366f1"],
                },
                "payment_states"
            );
            const instance = new window.ApexCharts(this.payChartRef.el, options);
            instance.render();
            this._charts.push(instance);
        }

        namedBar(this.topChartRef, data.top_customers, "top_customers");
        namedBar(this.itemsChartRef, data.top_items, "top_items");
        namedBar(this.catChartRef, data.top_categories, "top_categories");
        namedBar(this.salespersonChartRef, data.sales_by_salesperson, "salesperson");
        namedBar(this.brandChartRef, data.sales_by_brand, "brand");
        namedBar(this.countryChartRef, data.sales_by_country, "country");
        namedBar(this.portChartRef, data.sales_by_port, "port");
        namedBar(this.termsChartRef, data.payment_terms, "payment_terms");

        if (this.containerChartRef.el && data.container_types?.length) {
            const options = this._withClick(
                {
                    chart: { type: "donut", height: 300, toolbar: { show: false } },
                    labels: data.container_types.map((r) => r.label),
                    series: data.container_types.map((r) => r.value || 0),
                    legend: { position: "bottom" },
                },
                "container_types"
            );
            const instance = new window.ApexCharts(this.containerChartRef.el, options);
            instance.render();
            this._charts.push(instance);
        }

        if (this.agingChartRef.el && data.aging_buckets) {
            const agingLabels = Object.keys(data.aging_buckets);
            const options = this._withClick(
                {
                    chart: { type: "bar", height: 300, toolbar: { show: false } },
                    dataLabels: { enabled: false },
                    xaxis: { categories: agingLabels },
                    series: [{ name: "Amount", data: agingLabels.map((k) => data.aging_buckets[k] || 0) }],
                    colors: ["#ef4444"],
                },
                "aging"
            );
            const instance = new window.ApexCharts(this.agingChartRef.el, options);
            instance.render();
            this._charts.push(instance);
        }

        if (this.paidOpenChartRef.el && data.series?.paid_open?.labels?.length) {
            const options = this._withClick(
                {
                    chart: { type: "bar", height: 300, stacked: true, toolbar: { show: false } },
                    dataLabels: { enabled: false },
                    xaxis: { categories: data.series.paid_open.labels },
                    series: [
                        { name: "Paid", data: data.series.paid_open.paid || [] },
                        { name: "Open", data: data.series.paid_open.open || [] },
                    ],
                    colors: ["#10b981", "#f59e0b"],
                },
                "paid_open"
            );
            const instance = new window.ApexCharts(this.paidOpenChartRef.el, options);
            instance.render();
            this._charts.push(instance);
        }

        if (this.refundChartRef.el && data.series?.refunds?.total?.length) {
            const options = this._withClick(
                {
                    chart: { type: "line", height: 300, toolbar: { show: false } },
                    stroke: { curve: "smooth", width: 3 },
                    dataLabels: { enabled: false },
                    xaxis: { categories: labels },
                    series: [{ name: "Refunds", data: data.series.refunds.total || [] }],
                    colors: ["#ef4444"],
                },
                "refunds"
            );
            const instance = new window.ApexCharts(this.refundChartRef.el, options);
            instance.render();
            this._charts.push(instance);
        }

        if (this.marginChartRef.el && data.series?.margin?.total?.length) {
            const options = this._withClick(
                {
                    chart: { type: "area", height: 300, toolbar: { show: false } },
                    stroke: { curve: "smooth", width: 2 },
                    dataLabels: { enabled: false },
                    xaxis: { categories: labels },
                    series: [{ name: "Margin", data: data.series.margin.total || [] }],
                    colors: ["#22c55e"],
                },
                "margin"
            );
            const instance = new window.ApexCharts(this.marginChartRef.el, options);
            instance.render();
            this._charts.push(instance);
        }

        if (this.cohortChartRef.el && data.series?.cohort?.labels?.length) {
            const options = this._withClick(
                {
                    chart: { type: "bar", height: 300, stacked: true, toolbar: { show: false } },
                    dataLabels: { enabled: false },
                    xaxis: { categories: data.series.cohort.labels || [] },
                    grid: { strokeDashArray: 4, borderColor: "#e6e9ef" },
                    series: [
                        { name: "New", data: data.series.cohort.new || [] },
                        { name: "Returning", data: data.series.cohort.returning || [] },
                    ],
                },
                "cohort"
            );
            const instance = new window.ApexCharts(this.cohortChartRef.el, options);
            instance.render();
            this._charts.push(instance);
        }
    }

    formatCurrency(value) {
        const data = this.state.data;
        if (!data) {
            return value || 0;
        }
        const symbol = data.currency.symbol || "";
        const formatted = (value || 0).toLocaleString(undefined, {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        });
        return data.currency.position === "after" ? `${formatted} ${symbol}` : `${symbol} ${formatted}`;
    }

    formatPercent(value) {
        const val = value || 0;
        return `${val.toFixed(1)}%`;
    }

    formatNumber(value) {
        return (value || 0).toLocaleString();
    }
}

export class SalesDashboardAction extends Component {
    static template = "sales_customization.SalesDashboardAction";
    static components = { WithSearch, SalesDashboard };
    static props = { ...standardActionServiceProps };

    setup() {
        this.orm = useService("orm");
        this.state = useState({
            ready: false,
            withSearchProps: null,
        });

        onWillStart(async () => {
            const searchViewId = await this._getSearchViewId();
            const context = { ...(this.props.action.context || {}) };
            // Prefer confirmed orders by default for dashboard KPIs
            if (!context.search_default_sales && context.search_default_sales !== 0) {
                context.search_default_sales = 1;
            }
            this.state.withSearchProps = {
                resModel: "sale.order",
                searchViewId,
                context,
                domain: this.props.action.domain || [],
                globalState: this.props.globalState,
                loadIrFilters: true,
                searchMenuTypes: ["filter", "groupBy", "favorite"],
                display: {
                    controlPanel: {},
                    searchPanel: false,
                },
            };
            this.state.ready = true;
        });
    }

    async _getSearchViewId() {
        // Prefer action params (set on the client action / partner opener).
        // Never read ir.model.data from JS — non-admin users lack that ACL.
        const fromParams = this.props.action.params?.search_view_id;
        if (fromParams) {
            return fromParams;
        }
        try {
            return await this.orm.call(
                "res.partner",
                "get_sales_dashboard_search_view_id",
                []
            );
        } catch (_err) {
            return false;
        }
    }
}

registry.category("actions").add("sales_customization.sales_dashboard", SalesDashboardAction);
