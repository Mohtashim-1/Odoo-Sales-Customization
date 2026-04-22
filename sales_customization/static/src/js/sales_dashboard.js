/** @odoo-module **/

import { Component, onMounted, onPatched, onWillStart, useRef, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class SalesDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.state = useState({
            loading: true,
            data: null,
            partners: [],
            filters: {
                partnerId: this.props.action?.context?.partner_id || "",
                startDate: "",
                endDate: "",
            },
        });
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

        onWillStart(async () => {
            await this._loadPartners();
            await this._loadData();
        });

        onMounted(() => this._renderCharts());
        onPatched(() => this._renderCharts());
    }

    async _loadPartners() {
        const partners = await this.orm.searchRead(
            "res.partner",
            [["customer_rank", ">", 0]],
            ["name"],
            { limit: 200, order: "name asc" }
        );
        this.state.partners = partners;
    }

    async _loadData() {
        const { partnerId, startDate, endDate } = this.state.filters;
        const normalizedPartnerId = partnerId ? parseInt(partnerId, 10) : false;
        this.state.loading = true;
        this.state.data = await this.orm.call(
            "res.partner",
            "get_sales_dashboard_data",
            [normalizedPartnerId || false, startDate || false, endDate || false]
        );
        this.state.loading = false;
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
    }

    _renderCharts() {
        if (this.state.loading) {
            return;
        }
        if (!window.ApexCharts) {
            return;
        }
        this._destroyCharts();
        const data = this.state.data;
        if (!data) {
            return;
        }

        const labels = data.labels || [];
        const charts = [
            {
                ref: this.soChartRef,
                title: "Sales Orders",
                series: data.series.sale_orders,
            },
            {
                ref: this.invChartRef,
                title: "Sales Invoices",
                series: data.series.sale_invoices,
            },
            {
                ref: this.oldChartRef,
                title: "Historical (Old) Sales",
                series: data.series.old_sales,
            },
        ];

        for (const chart of charts) {
            if (!chart.ref.el) {
                continue;
            }
            const options = {
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
                legend: { position: "top", fontSize: "12px" },
                series: [
                    {
                        name: "Count",
                        type: "column",
                        data: chart.series.count,
                    },
                    {
                        name: "Amount",
                        type: "line",
                        data: chart.series.total,
                    },
                ],
                tooltip: {
                    shared: true,
                    intersect: false,
                },
            };
            const instance = new window.ApexCharts(chart.ref.el, options);
            instance.render();
            this._charts.push(instance);
        }

        if (this.payChartRef.el && data.payment_states?.length) {
            const labels = data.payment_states.map((item) => item.label);
            const values = data.payment_states.map((item) => item.value);
            const options = {
                chart: { type: "donut", height: 300 },
                labels,
                legend: { position: "bottom", fontSize: "12px" },
                series: values,
                dataLabels: { enabled: true },
                tooltip: {
                    y: {
                        formatter: (val) => val.toLocaleString(),
                    },
                },
            };
            const instance = new window.ApexCharts(this.payChartRef.el, options);
            instance.render();
            this._charts.push(instance);
        }

        if (this.topChartRef.el && data.top_customers?.length) {
            const labels = data.top_customers.map((item) => item.name);
            const values = data.top_customers.map((item) => item.total);
            const options = {
                chart: { type: "bar", height: 300 },
                plotOptions: { bar: { horizontal: true } },
                dataLabels: { enabled: false },
                xaxis: { categories: labels },
                grid: { strokeDashArray: 4, borderColor: "#e6e9ef" },
                series: [{ name: "Sales", data: values }],
            };
            const instance = new window.ApexCharts(this.topChartRef.el, options);
            instance.render();
            this._charts.push(instance);
        }

        if (this.itemsChartRef.el && data.top_items?.length) {
            const labels = data.top_items.map((item) => item.name);
            const values = data.top_items.map((item) => item.total);
            const options = {
                chart: { type: "bar", height: 300 },
                plotOptions: { bar: { horizontal: true } },
                dataLabels: { enabled: false },
                xaxis: { categories: labels },
                grid: { strokeDashArray: 4, borderColor: "#e6e9ef" },
                series: [{ name: "Sales", data: values }],
            };
            const instance = new window.ApexCharts(this.itemsChartRef.el, options);
            instance.render();
            this._charts.push(instance);
        }

        if (this.catChartRef.el && data.top_categories?.length) {
            const labels = data.top_categories.map((item) => item.name);
            const values = data.top_categories.map((item) => item.total);
            const options = {
                chart: { type: "bar", height: 300 },
                plotOptions: { bar: { horizontal: true } },
                dataLabels: { enabled: false },
                xaxis: { categories: labels },
                grid: { strokeDashArray: 4, borderColor: "#e6e9ef" },
                series: [{ name: "Sales", data: values }],
            };
            const instance = new window.ApexCharts(this.catChartRef.el, options);
            instance.render();
            this._charts.push(instance);
        }

        if (this.containerChartRef.el && data.container_types?.length) {
            const labels = data.container_types.map((item) => item.label);
            const values = data.container_types.map((item) => item.value);
            const options = {
                chart: { type: "pie", height: 300 },
                labels,
                legend: { position: "bottom", fontSize: "12px" },
                series: values,
                dataLabels: { enabled: true },
                tooltip: {
                    y: {
                        formatter: (val) => val.toLocaleString(),
                    },
                },
            };
            const instance = new window.ApexCharts(this.containerChartRef.el, options);
            instance.render();
            this._charts.push(instance);
        }

        if (this.agingChartRef.el && data.aging_buckets) {
            const labels = ["0-30", "31-60", "61-90", "90+"];
            const values = labels.map((label) => data.aging_buckets[label] || 0);
            const options = {
                chart: { type: "bar", height: 300 },
                dataLabels: { enabled: false },
                xaxis: { categories: labels },
                grid: { strokeDashArray: 4, borderColor: "#e6e9ef" },
                series: [{ name: "Outstanding", data: values }],
            };
            const instance = new window.ApexCharts(this.agingChartRef.el, options);
            instance.render();
            this._charts.push(instance);
        }

        if (this.salespersonChartRef.el && data.sales_by_salesperson?.length) {
            const labels = data.sales_by_salesperson.map((item) => item.name);
            const values = data.sales_by_salesperson.map((item) => item.total);
            const options = {
                chart: { type: "bar", height: 300 },
                plotOptions: { bar: { horizontal: true } },
                dataLabels: { enabled: false },
                xaxis: { categories: labels },
                grid: { strokeDashArray: 4, borderColor: "#e6e9ef" },
                series: [{ name: "Sales", data: values }],
            };
            const instance = new window.ApexCharts(this.salespersonChartRef.el, options);
            instance.render();
            this._charts.push(instance);
        }

        if (this.brandChartRef.el && data.sales_by_brand?.length) {
            const labels = data.sales_by_brand.map((item) => item.name);
            const values = data.sales_by_brand.map((item) => item.total);
            const options = {
                chart: { type: "bar", height: 300 },
                plotOptions: { bar: { horizontal: true } },
                dataLabels: { enabled: false },
                xaxis: { categories: labels },
                grid: { strokeDashArray: 4, borderColor: "#e6e9ef" },
                series: [{ name: "Sales", data: values }],
            };
            const instance = new window.ApexCharts(this.brandChartRef.el, options);
            instance.render();
            this._charts.push(instance);
        }

        if (this.countryChartRef.el && data.sales_by_country?.length) {
            const labels = data.sales_by_country.map((item) => item.name);
            const values = data.sales_by_country.map((item) => item.total);
            const options = {
                chart: { type: "bar", height: 300 },
                plotOptions: { bar: { horizontal: true } },
                dataLabels: { enabled: false },
                xaxis: { categories: labels },
                grid: { strokeDashArray: 4, borderColor: "#e6e9ef" },
                series: [{ name: "Sales", data: values }],
            };
            const instance = new window.ApexCharts(this.countryChartRef.el, options);
            instance.render();
            this._charts.push(instance);
        }

        if (this.portChartRef.el && data.sales_by_port?.length) {
            const labels = data.sales_by_port.map((item) => item.name);
            const values = data.sales_by_port.map((item) => item.total);
            const options = {
                chart: { type: "bar", height: 300 },
                plotOptions: { bar: { horizontal: true } },
                dataLabels: { enabled: false },
                xaxis: { categories: labels },
                grid: { strokeDashArray: 4, borderColor: "#e6e9ef" },
                series: [{ name: "Sales", data: values }],
            };
            const instance = new window.ApexCharts(this.portChartRef.el, options);
            instance.render();
            this._charts.push(instance);
        }

        if (this.termsChartRef.el && data.payment_terms?.length) {
            const labels = data.payment_terms.map((item) => item.name);
            const values = data.payment_terms.map((item) => item.total);
            const options = {
                chart: { type: "pie", height: 300 },
                labels,
                legend: { position: "bottom", fontSize: "12px" },
                series: values,
                dataLabels: { enabled: true },
            };
            const instance = new window.ApexCharts(this.termsChartRef.el, options);
            instance.render();
            this._charts.push(instance);
        }

        if (this.paidOpenChartRef.el && data.series?.paid_open?.labels?.length) {
            const labels = data.series.paid_open.labels || [];
            const options = {
                chart: { type: "area", height: 300, stacked: false },
                stroke: { curve: "smooth" },
                dataLabels: { enabled: false },
                xaxis: { categories: labels },
                grid: { strokeDashArray: 4, borderColor: "#e6e9ef" },
                series: [
                    { name: "Paid", data: data.series.paid_open.paid || [] },
                    { name: "Open", data: data.series.paid_open.open || [] },
                ],
            };
            const instance = new window.ApexCharts(this.paidOpenChartRef.el, options);
            instance.render();
            this._charts.push(instance);
        }

        if (this.refundChartRef.el && data.series?.refunds?.labels?.length) {
            const labels = data.series.refunds.labels || [];
            const options = {
                chart: { type: "line", height: 300 },
                stroke: { curve: "smooth" },
                dataLabels: { enabled: false },
                xaxis: { categories: labels },
                grid: { strokeDashArray: 4, borderColor: "#e6e9ef" },
                series: [
                    { name: "Refunds", data: data.series.refunds.total || [] },
                ],
            };
            const instance = new window.ApexCharts(this.refundChartRef.el, options);
            instance.render();
            this._charts.push(instance);
        }

        if (this.marginChartRef.el && data.series?.margin?.labels?.length) {
            const labels = data.series.margin.labels || [];
            const options = {
                chart: { type: "line", height: 300 },
                stroke: { curve: "smooth" },
                dataLabels: { enabled: false },
                xaxis: { categories: labels },
                grid: { strokeDashArray: 4, borderColor: "#e6e9ef" },
                series: [
                    { name: "Margin", data: data.series.margin.total || [] },
                ],
            };
            const instance = new window.ApexCharts(this.marginChartRef.el, options);
            instance.render();
            this._charts.push(instance);
        }

        if (this.cohortChartRef.el && data.series?.cohort?.labels?.length) {
            const labels = data.series.cohort.labels || [];
            const options = {
                chart: { type: "bar", height: 300, stacked: true },
                dataLabels: { enabled: false },
                xaxis: { categories: labels },
                grid: { strokeDashArray: 4, borderColor: "#e6e9ef" },
                series: [
                    { name: "New", data: data.series.cohort.new || [] },
                    { name: "Returning", data: data.series.cohort.returning || [] },
                ],
            };
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

    async onApplyFilters() {
        await this._loadData();
        this._renderCharts();
    }

    async onResetFilters() {
        this.state.filters.startDate = "";
        this.state.filters.endDate = "";
        if (!this.props.action?.context?.partner_id) {
            this.state.filters.partnerId = "";
        } else {
            this.state.filters.partnerId = this.props.action.context.partner_id;
        }
        await this._loadData();
        this._renderCharts();
    }
}

SalesDashboard.template = "sales_customization.SalesDashboard";

registry.category("actions").add("sales_customization.sales_dashboard", SalesDashboard);
