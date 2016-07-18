/**
 * Date range picker.
 */

'use strict';

require('pikaday-css');

var oop = require('js/oop');
var pikaday = require('pikaday');


var DateRangePicker = oop.defclass({
    constructor: function(params) {
        var self = this;

        self.minDate = params.minDate;
        self.maxDate = params.maxDate;

        self.startDate = params.startDate;
        self.startPickerElem = params.startPickerElem;
        self._startPicker = self._makePicker(params.startPickerElem, 'startDate', 'updateStartDate');

        self.endDate = params.endDate;
        self.endPickerElem = params.endPickerElem;
        self._endPicker = self._makePicker(params.endPickerElem, 'endDate', 'updateEndDate');

        self.updateStartDate(self.startDate);
        self.updateEndDate(self.endDate);
    },
    _makePicker: function(pickerElem, dateProp, updateDateFunc) {
        var self = this;
        return new pikaday({
            bound: true,
            field: pickerElem,
            defaultDate: self[dateProp],
            setDefaultDate: true,
            minDate: self.minDate,
            maxDate: self.maxDate,
            onSelect: function() {
                self[dateProp] = this.getDate();
                self[updateDateFunc](self[dateProp]);
                pickerElem.value = this.toString();
            }
        });
    },
    updateStartDate: function(start) {
        var self = this;
        self._startPicker.setStartRange(start);
        self._endPicker.setStartRange(start);
        self._endPicker.setMinDate(start);
    },
    updateEndDate: function(end) {
        var self = this;
        self._startPicker.setEndRange(end);
        self._startPicker.setMaxDate(end);
        self._endPicker.setEndRange(end);
    },
});


module.exports = DateRangePicker;
