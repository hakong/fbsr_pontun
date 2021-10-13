
import React from 'react';
import {
  Switch,
  Route,
  Link,
  useRouteMatch
} from "react-router-dom";
	import { sort, CaretUp, CaretDown } from './misc.js';

export function PaymentsPage(props) {
	let { url } = useRouteMatch();
	//let params = useParams();
	/*<Route path={`${url}/edit/:memberId`}>
	//	<AddPayment listing={props.listing} url={url} params={params} />
	//</Route>
	*/
	return (
		<Switch>
			<Route path={`${url}/add/:memberId`} render={({ match, history }) => <AddPayment listing={props.listing} match={match} parentUrl={url} history={history} />} />
			<Route path={`${url}/email`} render={({ match, history }) => <Email listing={props.listing} match={match} parentUrl={url} history={history} />} />
			<Route path={url}>
				<Payments listing={props.listing} url={url} />
			</Route>
		</Switch>
	);

}

class Email extends React.Component {
	constructor(props) {
		super(props);
		this.state = {
			auth_token: "Bearer " + new URLSearchParams(window.location.search).get("token"),
			sample: "",
			samples: null,
			candidates: null,
			candidates_choice: [],
			template: null,
			template_changed: false,
			template_rendered: null,
			template_renderfor: null,
			subject: ""
		}
		//this.handleClick       = this.handleClick.bind(this);
		this.handleInputChange = this.handleInputChange.bind(this);
		this.handleSampleChange    = this.handleSampleChange.bind(this);
		this.handleTemplateChange  = this.handleTemplateChange.bind(this);
		this.handleCandidateChange = this.handleCandidateChange.bind(this);
		this.handleRenderforChange = this.handleRenderforChange.bind(this);
		this.updateTemplateRender  = this.updateTemplateRender.bind(this);
		this.rerenderTemplate      = this.rerenderTemplate.bind(this);
		this.sendEmail             = this.sendEmail.bind(this);
	}

	reload() {
		fetch("/api/listing/" + this.props.listing.id + "/payments/email", {headers: {'Authorization': this.state.auth_token}})
			.then(res => res.json())
			.then(
				(results) => this.setState(results)
			);
	}
	componentDidMount() { this.reload(); }

	handleSampleChange(event) {
		let value = event.target.value;
		if (value === "") {
			this.setState({candidates: null, sample: "", template: null, candidates_choice: [], template_rendered: null, template_renderfor: null});
		} else {
			console.log("Setting sample value", value)
			fetch("/api/listing/" + this.props.listing.id + "/payments/email", {method: "POST", headers: {'Authorization': this.state.auth_token, 'Content-Type': 'application/json'}, body: JSON.stringify({sample: value})})
				.then(res => res.json())
				.then(
					(results) => this.setState(results)
				);
		}
	}

	rerenderTemplate() {
		fetch("/api/listing/" + this.props.listing.id + "/payments/email", {method: "POST", headers: {'Authorization': this.state.auth_token, 'Content-Type': 'application/json'}, body: JSON.stringify({
				sample: this.state.sample,
				template_renderfor: this.state.template_renderfor,
				template: this.state.template
			})})
				.then(res => res.json())
				.then(
					(results) => this.setState({...results, ...{template_changed: false}})
				);
	}

	sendEmail(event) {
		let self = this;
		if (window.confirm("Ertu viss um að þú viljir senda tölvupóst á " + this.state.candidates_choice.length + " manns?")) {
			fetch("/api/listing/" + this.props.listing.id + "/payments/email", {method: "POST", headers: {'Authorization': this.state.auth_token, 'Content-Type': 'application/json'}, body: JSON.stringify({
					subject: this.state.subject,
					sample: this.state.sample,
					template_renderfor: this.state.template_renderfor,
					template: this.state.template,
					candidates_choice: this.state.candidates_choice,
					send: true
				})})
					.then((results) => self.props.history.push(self.props.parentUrl + window.location.search));
		}
		event.stopPropagation();
		event.preventDefault();
	}

	updateTemplateRender(event) {
		this.rerenderTemplate();
		event.stopPropagation();
		event.preventDefault();
	}


	handleCandidateChange(event) { 
		console.log(event, event.target.selectedOptions);
		let values = Array.from(event.target.selectedOptions, (val, key) => parseInt(val.value));
		console.log(values);
		this.setState({candidates_choice: values}); 
	}
	handleInputChange(event) { this.setState({[event.target.name]: event.target.value}); }
	handleTemplateChange(event) { this.setState({template: event.target.value, template_changed: true}); }
	handleRenderforChange(event) { 
		this.setState({
			template_renderfor: event.target.value, 
			template_changed: true
		}, this.rerenderTemplate); 
	}

	render() {
		if (this.state.samples === null)
			return "";

		let sample_choices = this.state.samples.map((value, key) => <option key={value[0]} value={value[0]}>{value[1]}</option>); 
		sample_choices.unshift(<option key="" value="">(ekkert valið)</option>);

		let candidates = null;
		if (this.state.candidates !== null)
			candidates = this.state.candidates.map((value, key) => <option key={value.id} value={value.id}>{value.name}</option>); 

		return <div>
			<h3>Uppgjör - Senda tölvupóst</h3>
			<p>Hér er hægt að senda tölvupóst á meðlimi pöntunar.</p>
			<form>
				<div className="form-group row">
					<label htmlFor="sample" className="col-sm-2 col-form-label">Úrtak</label>
					<div className="col-sm-10">
						<select name="sample" className="form-control" id="sample" value={this.state.sample} onChange={this.handleSampleChange}>
							{sample_choices}
						</select>
					</div>
				</div>
				
				{ this.state.candidates !== null && 
					<div className="form-group row">
						<label htmlFor="candidates" className="col-sm-2 col-form-label">Viðtakendur</label>
						<div className="col-sm-10">
							<select name="candidates_choice" className="form-control custom-select" id="candidates_choice" value={this.state.candidates_choice} onChange={this.handleCandidateChange} multiple="multiple" size={Math.min(this.state.candidates.length, 20)}>
								{candidates}
							</select>
						</div>
					</div>
				}

				{ this.state.template !== null && 
					<div>
						<div className="form-group row">
							<label htmlFor="subject" className="col-sm-2 col-form-label">Subject</label>
							<div className="col-sm-10">
								<input className="form-control" pattern=".{5,}" style={{fontFamily: 'monospace'}} name="subject" value={this.state.subject} onChange={this.handleInputChange} type="text" />
							</div>
						</div>
						<div className="form-group row">
							<label htmlFor="template" className="col-sm-2 col-form-label">Sniðmát</label>
							<div className="col-sm-10">
								<textarea className="form-control" style={{fontFamily: 'monospace'}} name="template" value={this.state.template} onChange={this.handleTemplateChange} rows={20}></textarea>
							</div>
						</div>
						<div className="form-group row">
							<label htmlFor="template_renderfor" className="col-sm-2 col-form-label">Sjá dæmi um tölvupóst til</label>
							<div className="col-sm-10">
								<select name="template_renderfor" className="form-control" id="template_renderfor" value={this.state.template_renderfor} onChange={this.handleRenderforChange}>
									{candidates}
								</select>
							</div>
						</div>
						<div className="form-group row">
							<label htmlFor="template" className="col-sm-2 col-form-label">Dæmi <button className="btn btn-sm btn-info" onClick={this.updateTemplateRender} disabled={!this.state.template_changed} >Uppfæra</button></label>
							<div className="col-sm-10">
								<textarea className="form-control" style={{fontFamily: 'monospace'}} name="template_rendered" value={this.state.template_rendered} rows={20} readOnly={true}></textarea>
							</div>
						</div>
						<button className="btn btn-danger" onClick={this.sendEmail} disabled={this.state.candidates_choice.length < 1 || this.state.subject.length < 1}>Senda á {this.state.candidates_choice.length} manns</button>
					</div>
				}

			</form>

			</div>;
	}
}

export class AddPayment extends React.Component {
	constructor(props) {
		super(props);
		this.state = {
			date: (new Date()).toISOString().substr(0,10),
			time: (new Date()).toISOString().substr(11,8),
			amount: 0,
			comments: "",
			auth_token: "Bearer " + new URLSearchParams(window.location.search).get("token")
		}
		this.handleClick       = this.handleClick.bind(this);
		this.handleInputChange = this.handleInputChange.bind(this);
	}

	handleClick(event) {
		let self = this;
		fetch("/api/listing/" + this.props.listing.id + "/payments", {method: "POST", headers: {'Authorization': this.state.auth_token, 'Content-Type': 'application/json'}, body: JSON.stringify({
				member_id: this.props.match.params.memberId,
				time: this.state.date + "T" + this.state.time,
				amount: this.state.amount,
				comment: this.state.comment
		})})
			.then(res => res.json())
			.then(
					(results) => self.props.history.push(self.props.parentUrl + window.location.search)
			);

		event.stopPropagation();
		event.preventDefault();
	}

	handleInputChange(event) {
		this.setState({[event.target.name]: event.target.value});
	}

	render() {
		return (<div>
			<h3>Skrá millifærslu</h3>
			<form>
				<div className="form-group row">
					<label htmlFor="arrival" className="col-sm-2 col-form-label">Tími millifærslu</label>
					<div className="col-sm-4">
						<input name="date" type="date"  className="form-control" id="arrival" value={this.state.date} onChange={this.handleInputChange} />
					</div>
					<div className="col-sm-4">
						<input name="time" type="time"  className="form-control" id="arrival" value={this.state.time} onChange={this.handleInputChange} />
					</div>
				</div>
				<div className="form-group row">
					<label htmlFor="cost" className="col-sm-2 col-form-label">Upphæð</label>
					<div className="col-sm-4">
						<input name="amount" type="number" className="form-control" id="cost" value={this.state.amount} onChange={this.handleInputChange} />
					</div>
					<div className="col-sm-2"><p className="my-1">ISK</p></div>
				</div>
				<div className="form-group row">
					<label htmlFor="comment" className="col-sm-2 col-form-label">Athugasemdir</label>
					<div className="col-sm-8">
						<textarea name="comment" className="form-control" id="comment" rows="3" value={this.state.comment} onChange={this.handleInputChange}></textarea>
					</div>
				</div>
				<button type="submit" className="btn btn-primary" onClick={this.handleClick}>Skrá</button>
			</form>
		</div>);
	}
}

function SinglePaymentEntry(props) {
	return <tr>
		<td key="time">{props.payment.time}</td>
		<td key="amount">{props.payment.amount}</td>
		<td key="comment">{props.payment.comment}</td>
		<td key="actions">
			<button onClick={(e) => props.handleDelete(e, props.payment.id)} className="btn btn-warning btn-sm">Eyða færslu</button>
		</td>
	</tr>;
}


export class PaymentMemberEntry extends React.Component {
	constructor(props) {
		super(props);
		this.state = {
			details_visible: false,
			auth_token: "Bearer " + new URLSearchParams(window.location.search).get("token")
		}
		this.handleClick     = this.handleClick.bind(this);
	}

	handleClick(event) { this.setState({details_visible: ~this.state.details_visible}); }

	render() {
		const payments = this.props.member.payments.map((value, key) => <SinglePaymentEntry key={value.id} payment={value} handleDelete={this.props.handleDeletePayment} />);

		let details = null;
		if (this.state.details_visible) {
			details = <tr key="details"><td colSpan={7}>
				<table className="table table-sm">
					<thead>
						<tr>
							<th key="time">Tími</th>
							<th key="amount">Upphæð</th>
							<th key="comment">Athugasemd</th>
							<th key="actions"></th>
						</tr>
					</thead>
					<tbody>
						{payments}
					</tbody>
				</table>
			</td></tr>
		}

		let clr = "";
		if (this.props.member.remainder === 0) {
			clr = "table-success";
		} else if (this.props.member.remainder < 0) {
			clr = "table-warning";
		} else {
			clr = "table-danger";
		}

		return <tbody>
				<tr className={clr} key="member" onClick={this.handleClick}>
					<td key="name">{this.props.member.name}</td>
					<td key="email">{this.props.member.email}</td>
					<td key="estimate">{this.props.member.estimated_cost.toLocaleString()} kr</td>
					<td key="total">{this.props.member.total_cost.toLocaleString()} kr</td>
					<td key="payments">{this.props.member.total_payments.toLocaleString()} kr</td>
					<td key="remainder">{this.props.member.remainder.toLocaleString()} kr ({ this.props.member.remainder > 0 ? 'skuld' : 'inneign'})</td>
					<td key="actions"><Link className="btn btn-primary btn-sm" to={{pathname: `${this.props.url}/add/${this.props.member.id}`, search: window.location.search}}>Skrá millifærslu</Link></td>
				</tr>
				{details}
			</tbody>;
	}
}

export class Payments extends React.Component {
	constructor(props) {
		super(props);
		this.state = {
			auth_token: "Bearer " + new URLSearchParams(window.location.search).get("token"),
			members: null, 
			memberSortColumnDirection: "asc",
			memberSortColumn: "name"
		};
		this.reload              = this.reload.bind(this);
		this.handleMemberSort    = this.handleMemberSort.bind(this);
		this.handleDeletePayment = this.handleDeletePayment.bind(this);
	}

	reload() {
		fetch("/api/listing/" + this.props.listing.id + "/payments", {headers: {'Authorization': this.state.auth_token}})
			.then(res => res.json())
			.then(
				(results) => this.setState(results)
			);
	}
	componentDidMount() { this.reload(); }

	handleMemberSort(key) {
		if (key === this.state.memberSortColumn) {
			this.setState({"memberSortColumnDirection": this.state.memberSortColumnDirection === "asc" ? "desc" : "asc"});
		} else {
			this.setState({"memberSortColumn": key, "memberSortColumnDirection": "asc"});
		}
	}

	handleDeletePayment(e, id) {
		fetch("/api/listing/" + this.props.listing.id + "/payments/" + id, {headers: {'Authorization': this.state.auth_token}, method: "DELETE"})
			.then(res => this.reload());

	}

	render() {
		if (this.state.members === null) {
			return "";
		}
		const member_rows = this.state.members.sort((a, b) => (this.state.memberSortColumnDirection === "asc" ? 1 : -1)*sort(a[this.state.memberSortColumn], b[this.state.memberSortColumn])).map((value, key) => <PaymentMemberEntry reload={this.reload} url={this.props.url} key={value.id} member={value} handleDeletePayment={this.handleDeletePayment} />);

		const total_cost      = this.state.members.map((value, key) => value.total_cost).reduce((a, b) => a + b, 0);  
		const total_payments  = this.state.members.map((value, key) => value.total_payments).reduce((a, b) => a + b, 0);  
		const total_remainder = this.state.members.map((value, key) => value.remainder).reduce((a, b) => a + b, 0);  

		return <div>
			<h3>Kvittanir <Link className="btn btn-sm btn-primary" to={{pathname: `${this.props.url}/email`, search: window.location.search}}>Senda póst</Link></h3>
			<table className="table table-striped table-sm shipment-order">
				<thead>
					<tr>
						<th onClick={() => this.handleMemberSort('name')}     key="name"      >Nafn         {this.state.memberSortColumn === "name"          ? (this.state.memberSortColumnDirection === "asc" ? <CaretUp /> : <CaretDown />) : ''}</th>
						<th onClick={() => this.handleMemberSort('email')}    key="email"     >Netfang      {this.state.memberSortColumn === "email"         ? (this.state.memberSortColumnDirection === "asc" ? <CaretUp /> : <CaretDown />) : ''}</th>
						<th onClick={() => this.handleMemberSort('estimated_cost')}    key="estimate"     >Áætlað verð {this.state.memberSortColumn === "estimated_cost"           ? (this.state.memberSortColumnDirection === "asc" ? <CaretUp /> : <CaretDown />) : ''}</th>
						<th onClick={() => this.handleMemberSort('total_cost')}    key="total"     >Reiknað verð {this.state.memberSortColumn === "total_cost"           ? (this.state.memberSortColumnDirection === "asc" ? <CaretUp /> : <CaretDown />) : ''}</th>
						<th onClick={() => this.handleMemberSort('total_payments')} key="total_payments"  >Greiðslur  {this.state.memberSortColumn === "total_payments" ? (this.state.memberSortColumnDirection === "asc" ? <CaretUp /> : <CaretDown />) : ''}</th>
						<th onClick={() => this.handleMemberSort('remainder')} key="remainder">Eftirstöðvar{this.state.memberSortColumn === "remainder" ? (this.state.memberSortColumnDirection === "asc" ? <CaretUp /> : <CaretDown />) : ''}</th>
						<th></th>
					</tr>
				</thead>
				{member_rows}
				<thead>
					<tr>
						<th></th>
						<th></th>
						<th></th>
						<th>{total_cost.toLocaleString()} kr</th>
						<th>{total_payments.toLocaleString()} kr</th>
						<th>{total_remainder.toLocaleString()} kr</th>
					</tr>
				</thead>
			</table>

		</div>;
	}	
}
